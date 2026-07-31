/**
 * Contrôle de saisie côté client (JavaScript) — sans validation HTML5.
 * Active sur les formulaires .js-validate (attribut novalidate obligatoire).
 */
(function () {
  "use strict";

  const PHONE_RE = /^\+?[0-9][0-9\s\-()]{6,20}$/;
  const USERNAME_RE = /^[a-zA-Z0-9._-]{3,150}$/;
  const SERVER_NAME_RE = /^[a-zA-Z0-9][a-zA-Z0-9._-]{1,253}$/;
  const VERSION_RE = /^[a-zA-Z0-9][a-zA-Z0-9._+\-]{0,63}$/;
  const EMAIL_RE = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
  const URL_RE = /^https?:\/\/.+/i;
  const IPV4_RE =
    /^(25[0-5]|2[0-4]\d|1?\d?\d)(\.(25[0-5]|2[0-4]\d|1?\d?\d)){3}$/;
  const IPV6_RE = /^[0-9a-fA-F:]+$/;
  const PASSWORD_RE = /^(?=.*[A-Za-z])(?=.*\d).{8,}$/;

  function parseRules(el) {
    const raw = el.getAttribute("data-validate") || "";
    return raw
      .split("|")
      .map((r) => r.trim())
      .filter(Boolean);
  }

  function fieldWrapper(el) {
    return el.closest(".field") || el.parentElement;
  }

  function clearError(el) {
    el.classList.remove("is-invalid");
    const wrap = fieldWrapper(el);
    if (!wrap) return;
    wrap.querySelectorAll(".js-field-error").forEach((node) => node.remove());
  }

  function showError(el, message) {
    el.classList.add("is-invalid");
    const wrap = fieldWrapper(el);
    if (!wrap) return;
    let box = wrap.querySelector(".js-field-error");
    if (!box) {
      box = document.createElement("div");
      box.className = "js-field-error";
      wrap.appendChild(box);
    }
    box.textContent = message;
  }

  function valueOf(el) {
    if (el.type === "checkbox") return el.checked ? "1" : "";
    return (el.value || "").trim();
  }

  function validateRule(el, rule, form) {
    const value = valueOf(el);
    const [name, arg] = rule.split(":");

    switch (name) {
      case "required":
        if (!value) return "Ce champ est obligatoire.";
        break;
      case "min": {
        const min = Number(arg || 0);
        if (value && value.length < min) {
          return `Minimum ${min} caractères.`;
        }
        break;
      }
      case "max": {
        const max = Number(arg || 0);
        if (value && value.length > max) {
          return `Maximum ${max} caractères.`;
        }
        break;
      }
      case "email":
        if (value && !EMAIL_RE.test(value)) return "Adresse email invalide.";
        break;
      case "username":
        if (value && !USERNAME_RE.test(value)) {
          return "Identifiant invalide (3–150 : lettres, chiffres, . _ -).";
        }
        break;
      case "phone":
        if (value && !PHONE_RE.test(value)) {
          return "Téléphone invalide. Exemple : +216 71 000 000.";
        }
        break;
      case "password":
        if (value && !PASSWORD_RE.test(value)) {
          return "Mot de passe : 8+ caractères, au moins une lettre et un chiffre.";
        }
        break;
      case "url":
        if (value && !URL_RE.test(value)) return "URL invalide (http/https).";
        break;
      case "version":
        if (value && !VERSION_RE.test(value)) {
          return "Version invalide (ex. 16, 5.2.1).";
        }
        break;
      case "serverName":
        if (value && !SERVER_NAME_RE.test(value)) {
          return "Nom de serveur invalide.";
        }
        break;
      case "ip":
        if (value && !(IPV4_RE.test(value) || (value.includes(":") && IPV6_RE.test(value)))) {
          return "Adresse IP invalide.";
        }
        break;
      case "numberMin": {
        if (value !== "" && Number(value) < Number(arg || 0)) {
          return `La valeur doit être ≥ ${arg}.`;
        }
        break;
      }
      case "match": {
        const other = form.querySelector(`[name="${arg}"]`);
        if (other && valueOf(other) !== value) {
          return "Les valeurs ne correspondent pas.";
        }
        break;
      }
      case "dateAfter": {
        const other = form.querySelector(`[name="${arg}"]`);
        if (other && value && valueOf(other) && value < valueOf(other)) {
          return "Cette date doit être postérieure ou égale à la date de début.";
        }
        break;
      }
      default:
        break;
    }
    return null;
  }

  function validateField(el, form) {
    clearError(el);
    const rules = parseRules(el);
    for (const rule of rules) {
      const error = validateRule(el, rule, form);
      if (error) {
        showError(el, error);
        return false;
      }
    }
    return true;
  }

  function validateForm(form) {
    let ok = true;
    const fields = form.querySelectorAll("[data-validate]");
    fields.forEach((el) => {
      if (!validateField(el, form)) ok = false;
    });
    return ok;
  }

  function enhanceForm(form) {
    form.setAttribute("novalidate", "novalidate");
    form.classList.add("js-validate");

    form.querySelectorAll("[data-validate]").forEach((el) => {
      el.addEventListener("blur", () => validateField(el, form));
      el.addEventListener("input", () => {
        if (el.classList.contains("is-invalid")) validateField(el, form);
      });
      el.addEventListener("change", () => validateField(el, form));
    });

    form.addEventListener("submit", (event) => {
      if (!validateForm(form)) {
        event.preventDefault();
        event.stopPropagation();
        const firstInvalid = form.querySelector(".is-invalid");
        if (firstInvalid) firstInvalid.focus();
      }
    });
  }

  function init() {
    document.querySelectorAll("form.js-validate, form[data-js-validate]").forEach(enhanceForm);
    // Auto: forms de gestion APM (pas les deletes/toggles)
    document.querySelectorAll("form.panel form, .panel > form, .auth-card form, section.panel > form").forEach((form) => {
      if (form.querySelector("[data-validate]")) enhanceForm(form);
    });
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", init);
  } else {
    init();
  }
})();
