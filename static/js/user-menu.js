(() => {
  const toggle = document.getElementById("user-menu-toggle");
  const menu = document.getElementById("user-menu-dropdown");
  if (!toggle || !menu) return;

  const open = () => {
    menu.hidden = false;
    toggle.setAttribute("aria-expanded", "true");
    menu.classList.add("is-open");
  };

  const close = () => {
    menu.classList.remove("is-open");
    toggle.setAttribute("aria-expanded", "false");
    menu.hidden = true;
  };

  toggle.addEventListener("click", (event) => {
    event.stopPropagation();
    if (menu.hidden) open();
    else close();
  });

  document.addEventListener("click", (event) => {
    if (menu.hidden) return;
    if (event.target.closest(".user-menu")) return;
    close();
  });

  document.addEventListener("keydown", (event) => {
    if (event.key === "Escape" && !menu.hidden) {
      close();
      toggle.focus();
    }
  });
})();
