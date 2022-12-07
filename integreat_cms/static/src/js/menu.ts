document.addEventListener("DOMContentLoaded", () => {
    const mobile = document.querySelector("#mobile-menu");
    const sidebar = document.querySelector("#primary-navigation");

    mobile.addEventListener("click", () => {
        sidebar.classList.toggle("-translate-x-full");
    });
});
