(function () {
  "use strict";

  var PHONE = "34640997860";
  var LANGS = ["es", "en", "de"];
  var LANG_NAMES = { es: "Español", en: "English", de: "Deutsch" };
  var dict = window.SCR_I18N || {};
  var current = "es";

  /* ---------- Idiomas ---------- */
  // El HTML contiene el español: lo guardamos como referencia.
  var nodes = document.querySelectorAll("[data-i18n]");
  var attrNodes = document.querySelectorAll("[data-i18n-aria], [data-i18n-alt]");
  var perLangAlt = document.querySelectorAll("[data-alt-en], [data-alt-de]");
  var LOCALES = { es: "es-ES", en: "en-GB", de: "de-DE" };
  dict.es = dict.es || {};
  nodes.forEach(function (el) {
    var k = el.getAttribute("data-i18n");
    if (!(k in dict.es)) dict.es[k] = el.innerHTML.trim();
  });
  attrNodes.forEach(function (el) {
    var a = el.getAttribute("data-i18n-aria"), b = el.getAttribute("data-i18n-alt");
    if (a && !(a in dict.es)) dict.es[a] = el.getAttribute("aria-label");
    if (b && !(b in dict.es)) dict.es[b] = el.getAttribute("alt");
  });
  perLangAlt.forEach(function (el) { el.setAttribute("data-alt-es", el.getAttribute("alt") || ""); });
  var originalTitle = document.title;

  function t(key) {
    return (dict[current] && dict[current][key]) || dict.es[key] || "";
  }

  function store(key, val) { try { localStorage.setItem(key, val); } catch (e) {} }
  function read(key) { try { return localStorage.getItem(key); } catch (e) { return null; } }

  function setLang(lang) {
    if (LANGS.indexOf(lang) < 0) lang = "es";
    current = lang;
    document.documentElement.lang = lang;
    nodes.forEach(function (el) {
      var val = t(el.getAttribute("data-i18n"));
      if (val) el.innerHTML = val;
    });
    attrNodes.forEach(function (el) {
      var a = el.getAttribute("data-i18n-aria"), b = el.getAttribute("data-i18n-alt");
      if (a && t(a)) el.setAttribute("aria-label", t(a));
      if (b && t(b)) el.setAttribute("alt", t(b));
    });
    perLangAlt.forEach(function (el) {
      el.setAttribute("alt", el.getAttribute("data-alt-" + lang) || el.getAttribute("data-alt-es"));
    });
    // Fechas de los artículos en el formato de cada idioma
    document.querySelectorAll("time.js-date[datetime]").forEach(function (el) {
      var p = el.getAttribute("datetime").split("-");
      try {
        el.textContent = new Intl.DateTimeFormat(LOCALES[lang], { day: "numeric", month: "long", year: "numeric" })
          .format(new Date(+p[0], +p[1] - 1, +p[2]));
      } catch (e) {}
    });
    // Título de la pestaña
    var titleKey = document.body.getAttribute("data-title-key");
    var pageTitle = document.body.getAttribute("data-title-" + lang);
    if (titleKey) document.title = t(titleKey);
    else document.title = pageTitle || originalTitle;
    document.querySelectorAll(".lang-switch button").forEach(function (b) {
      b.setAttribute("aria-pressed", String(b.dataset.lang === lang));
    });
    updateWaLinks();
    store("scr-lang", lang);
  }

  function initialLang() {
    var q = new URLSearchParams(location.search).get("lang");
    if (q && LANGS.indexOf(q) >= 0) return q;
    var saved = read("scr-lang");
    if (saved && LANGS.indexOf(saved) >= 0) return saved;
    var nav = (navigator.language || "es").slice(0, 2).toLowerCase();
    return LANGS.indexOf(nav) >= 0 ? nav : "es";
  }

  document.querySelectorAll(".lang-switch button").forEach(function (b) {
    b.addEventListener("click", function () { setLang(b.dataset.lang); });
  });

  /* ---------- Enlaces de WhatsApp ---------- */
  function waUrl(text) {
    return "https://wa.me/" + PHONE + "?text=" + encodeURIComponent(text);
  }
  function updateWaLinks() {
    var url = waUrl(t("wa.prefill"));
    document.querySelectorAll(".js-wa, .js-wa-bubble").forEach(function (a) { a.href = url; });
  }

  /* ---------- Menú móvil ---------- */
  var toggle = document.querySelector(".nav-toggle");
  var nav = document.getElementById("main-nav");
  function closeNav() {
    if (!nav || !toggle) return;
    nav.classList.remove("open");
    toggle.setAttribute("aria-expanded", "false");
  }
  if (toggle && nav) {
    toggle.addEventListener("click", function () {
      var open = nav.classList.toggle("open");
      toggle.setAttribute("aria-expanded", String(open));
    });
    nav.querySelectorAll("a").forEach(function (a) { a.addEventListener("click", closeNav); });
  }

  /* ---------- Cabecera al hacer scroll ---------- */
  var header = document.querySelector(".site-header");
  function onScroll() { if (header) header.classList.toggle("scrolled", window.scrollY > 8); }
  window.addEventListener("scroll", onScroll, { passive: true });
  onScroll();

  /* ---------- Animación de aparición ---------- */
  var revealEls = document.querySelectorAll(".pillar, .treat-col, .cred, .step, .island, .news-card, .faq details, .booking-form");
  if ("IntersectionObserver" in window) {
    var io = new IntersectionObserver(function (entries) {
      entries.forEach(function (en) {
        if (en.isIntersecting) { en.target.classList.add("in"); io.unobserve(en.target); }
      });
    }, { threshold: 0.12 });
    revealEls.forEach(function (el) { el.classList.add("reveal"); io.observe(el); });
  }

  /* ---------- Formulario de cita ---------- */
  var form = document.getElementById("booking-form");
  if (form) initForm(form);

  function initForm(form) {
    var F = form.elements;
    var success = document.getElementById("form-success");
    var today = new Date();
    today.setMinutes(today.getMinutes() - today.getTimezoneOffset());
    F.date.min = today.toISOString().slice(0, 10);

    // Preseleccionar isla desde los enlaces de la página
    document.querySelectorAll("[data-island]").forEach(function (a) {
      a.addEventListener("click", function () {
        var r = form.querySelector('input[name="island"][value="' + a.dataset.island + '"]');
        if (r) r.checked = true;
      });
    });

    function setInvalid(el, bad) {
      var wrap = el.closest(".field");
      if (wrap) wrap.classList.toggle("invalid", bad);
    }

    function validate() {
      var ok = true, first = null;
      var island = form.querySelector('input[name="island"]:checked');
      var checks = [
        [F.name, F.name.value.trim().length >= 2],
        [F.phone, F.phone.value.replace(/\D/g, "").length >= 9],
        [form.querySelector('input[name="island"]'), !!island],
        [F.service, !!F.service.value]
      ];
      checks.forEach(function (c) {
        setInvalid(c[0], !c[1]);
        if (!c[1]) { ok = false; if (!first) first = c[0]; }
      });

      var consentErr = form.querySelector(".consent-error");
      consentErr.classList.toggle("show", !F.consent.checked);
      if (!F.consent.checked) { ok = false; if (!first) first = F.consent; }

      if (first) first.focus();
      return ok;
    }

    form.addEventListener("input", function (e) {
      var f = e.target.closest(".field");
      if (f && f.classList.contains("invalid")) setInvalid(e.target, false);
      if (e.target.name === "consent") form.querySelector(".consent-error").classList.remove("show");
    });
    form.addEventListener("change", function (e) {
      if (e.target.name === "island" || e.target.name === "service") setInvalid(e.target, false);
    });

    function optionLabelEs(select) {
      var opt = select.options[select.selectedIndex];
      var key = opt.getAttribute("data-i18n");
      var tmp = document.createElement("div");
      tmp.innerHTML = (key && dict.es[key]) || opt.textContent;
      return tmp.textContent.trim();
    }

    function formatDate(iso) {
      if (!iso) return "Sin preferencia";
      var p = iso.split("-");
      return p[2] + "/" + p[1] + "/" + p[0];
    }

    form.addEventListener("submit", function (e) {
      e.preventDefault();
      if (!validate()) return;

      // El mensaje llega a la consulta siempre en español, indicando el idioma del paciente.
      var lines = [
        "Hola Silvia, me gustaría *solicitar una cita* (pendiente de confirmación).",
        "",
        "• Nombre: " + F.name.value.trim(),
        "• Teléfono: " + F.phone.value.trim(),
        "• Isla: " + form.querySelector('input[name="island"]:checked').value,
        "• Motivo: " + optionLabelEs(F.service),
        "• Fecha preferida: " + formatDate(F.date.value),
        "• Franja: " + optionLabelEs(F.time)
      ];
      var msg = F.message.value.trim();
      if (msg) lines.push("• Comentario: " + msg);
      if (current !== "es") lines.push("• Idioma preferido: " + LANG_NAMES[current]);

      window.open(waUrl(lines.join("\n")), "_blank", "noopener");
      success.hidden = false;
      success.focus();
    });
  }

  /* ---------- Burbuja de WhatsApp ---------- */
  var widget = document.getElementById("wa-widget");
  var bubble = document.getElementById("wa-bubble");
  var panel = document.getElementById("wa-panel");
  function closeWa() {
    if (!panel || !bubble) return;
    panel.hidden = true;
    bubble.setAttribute("aria-expanded", "false");
  }
  if (widget && bubble && panel) {
    bubble.addEventListener("click", function () {
      if (panel.hidden) {
        panel.hidden = false;
        bubble.setAttribute("aria-expanded", "true");
        widget.classList.add("seen");
        store("scr-wa-seen", "1");
      } else {
        closeWa();
      }
    });
    document.getElementById("wa-close").addEventListener("click", closeWa);
    if (read("scr-wa-seen")) widget.classList.add("seen");
  }

  document.addEventListener("keydown", function (e) {
    if (e.key === "Escape") { closeNav(); closeWa(); }
  });

  /* ---------- Varios ---------- */
  document.querySelectorAll(".js-year").forEach(function (el) { el.textContent = new Date().getFullYear(); });

  setLang(initialLang());
})();
