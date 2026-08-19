(() => {
  const bindDropdown = ({ toggleId, menuId, rootSelector }) => {
    const toggle = document.getElementById(toggleId);
    const menu = document.getElementById(menuId);
    if (!toggle || !menu) return null;

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
      if (event.target.closest(rootSelector)) return;
      close();
    });

    document.addEventListener("keydown", (event) => {
      if (event.key === "Escape" && !menu.hidden) {
        close();
        toggle.focus();
      }
    });

    return { open, close, menu, toggle };
  };

  const user = bindDropdown({
    toggleId: "user-menu-toggle",
    menuId: "user-menu-dropdown",
    rootSelector: ".user-menu",
  });
  const notif = bindDropdown({
    toggleId: "notif-menu-toggle",
    menuId: "notif-menu-dropdown",
    rootSelector: ".notif-menu",
  });

  // Close the other dropdown when one opens
  if (user && notif) {
    user.toggle.addEventListener("click", () => {
      if (!notif.menu.hidden) notif.close();
    });
    notif.toggle.addEventListener("click", () => {
      if (!user.menu.hidden) user.close();
    });
  }
})();
