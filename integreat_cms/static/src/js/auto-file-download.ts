window.addEventListener("load", () => {
    document.querySelectorAll("[data-auto-download]").forEach((node) => {
        setTimeout(function () {
            (node as HTMLLinkElement).click();
        }, 500);
    });
});
