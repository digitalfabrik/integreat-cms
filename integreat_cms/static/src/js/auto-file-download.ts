//Clicks the auto-download link
// used in: pages_page_tree.html
window.addEventListener("load", () => {
    document.querySelectorAll("[data-auto-download]").forEach((node) => {
        const timeoutDuration = 500;
        setTimeout(() => {
            (node as HTMLLinkElement).click();
        }, timeoutDuration);
    });
});
