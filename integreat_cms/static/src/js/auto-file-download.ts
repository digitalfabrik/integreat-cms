window.addEventListener("load", () => {
    document.querySelectorAll("[data-auto-download]").forEach((node) => {
        const timeoutDuration = 500;
        setTimeout(() => {
            (node as HTMLLinkElement).click();
        }, timeoutDuration);
    });
});
