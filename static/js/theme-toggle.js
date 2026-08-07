/**
 * Topnet APM — light / dark theme toggle (localStorage: apm-theme).
 */
(function () {
  "use strict";

  var STORAGE_KEY = "apm-theme";

  function currentTheme() {
    return document.body.classList.contains("theme-dark") ? "dark" : "light";
  }

  function applyTheme(theme) {
    var isDark = theme === "dark";
    document.body.classList.toggle("theme-dark", isDark);
    try {
      localStorage.setItem(STORAGE_KEY, isDark ? "dark" : "light");
    } catch (e) {
      /* ignore */
    }
    document.querySelectorAll("[data-theme-toggle]").forEach(function (btn) {
      btn.setAttribute("aria-pressed", isDark ? "true" : "false");
      btn.setAttribute(
        "title",
        isDark ? "Passer en mode clair" : "Passer en mode sombre"
      );
      var label = btn.querySelector("[data-theme-label]");
      if (label) {
        label.textContent = isDark ? "Clair" : "Sombre";
      }
    });
  }

  function toggleTheme() {
    applyTheme(currentTheme() === "dark" ? "light" : "dark");
  }

  // Apply early preference (body may already have theme-dark from inline boot script)
  try {
    var saved = localStorage.getItem(STORAGE_KEY);
    if (saved === "dark" || saved === "light") {
      applyTheme(saved);
    } else {
      applyTheme(currentTheme());
    }
  } catch (e) {
    applyTheme("light");
  }

  document.addEventListener("click", function (event) {
    var btn = event.target.closest("[data-theme-toggle]");
    if (!btn) return;
    event.preventDefault();
    toggleTheme();
  });
})();
