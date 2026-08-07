/**
 * Auto-dismiss flash toasts after login / actions.
 */
(function () {
  "use strict";

  function dismiss(el) {
    if (!el) return;
    el.style.opacity = "0";
    el.style.transform = "translateY(-6px)";
    el.style.transition = "opacity 0.25s ease, transform 0.25s ease";
    window.setTimeout(function () {
      if (el.parentNode) el.parentNode.removeChild(el);
    }, 260);
  }

  document.addEventListener("DOMContentLoaded", function () {
    var items = document.querySelectorAll(".toast-item");
    items.forEach(function (item, index) {
      var closeBtn = item.querySelector(".toast-close");
      if (closeBtn) {
        closeBtn.addEventListener("click", function () {
          dismiss(item);
        });
      }
      window.setTimeout(function () {
        dismiss(item);
      }, 5500 + index * 400);
    });
  });
})();
