const switchLanguage = (language: string) => {
    document.querySelectorAll(".language-tab-header").forEach((tab) => {
        tab.classList.remove("z-10", "text-blue-500", "bg-white", "cursor-default");
        tab.classList.add("bg-water-500");
    });
    document.querySelectorAll(".language-tab-content").forEach((tab) => tab.classList.add("hidden"));

    document.getElementById(`tab-${language}`).classList.remove("hidden");
    document.getElementById(`li-${language}`).classList.remove("bg-water-500");
    document.getElementById(`li-${language}`).classList.add("z-10", "text-blue-500", "bg-white", "cursor-default");
};

const adjustTextDirection = (textDirection: string, language: string) => {
    if (textDirection === "RIGHT_TO_LEFT") {
        (document.querySelector(`#tab-${language} input`) as HTMLElement).dir = "rtl";
        (document.querySelector(`#tab-${language} textarea`) as HTMLElement).dir = "rtl";
    }
};

window.addEventListener("load", () => {
    document.querySelectorAll("[data-switch-language]").forEach((node) => {
        const nodeElement = node as HTMLElement;
        nodeElement.addEventListener("click", () => {
            switchLanguage(nodeElement.dataset.switchLanguage);
            adjustTextDirection(nodeElement.dataset.textDirection, nodeElement.dataset.switchLanguage);
        });
    });
});
