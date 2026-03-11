const applyCopyFeedback = (node: HTMLElement) => {
    const copy = node.querySelector("[icon-name=copy]");
    const check = node.querySelector("[icon-name=check]");

    if (copy && check) {
        copy.classList.add("hidden");
        check.classList.remove("hidden");

        const timeoutDuration = 3000;
        setTimeout(() => {
            copy.classList.remove("hidden");
            check.classList.add("hidden");
        }, timeoutDuration);
    }
};

export const copyToClipboard = (value: string) => {
    const tmpInput = document.createElement("input");
    const maxSelectionLength = 99_999;
    tmpInput.type = "text";
    document.body.appendChild(tmpInput);
    tmpInput.value = value;
    tmpInput.select();
    tmpInput.setSelectionRange(0, maxSelectionLength);

    document.execCommand("copy");
    document.body.removeChild(tmpInput);
};

window.addEventListener("load", () => {
    document.querySelectorAll("[data-copy-to-clipboard]").forEach((node) => {
        node.addEventListener("click", ({ currentTarget }) => {
            const value = (currentTarget as HTMLElement).getAttribute("data-copy-to-clipboard");
            copyToClipboard(value);
            applyCopyFeedback(currentTarget as HTMLElement);
        });
    });
});
