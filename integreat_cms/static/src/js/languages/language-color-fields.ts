const renderLanguageColorPreview = ({ target }: Event) => {
    const languageColorSelectFromChoices = target as HTMLSelectElement;
    const colorPreview = document.getElementById("language-color-preview");
    const selectedColor = languageColorSelectFromChoices.options[languageColorSelectFromChoices.selectedIndex].value;
    if (selectedColor) {
        colorPreview.style.backgroundColor = selectedColor;
        colorPreview.classList.remove("hidden");
        languageColorSelectFromChoices.classList.add("rounded-none", "rounded-r", "border-l-0");
    } else {
        colorPreview.classList.add("hidden");
        languageColorSelectFromChoices.classList.remove("rounded-none", "rounded-r", "border-l-0");
    }
};

window.addEventListener("load", () => {
    const languageColorSelect = document.getElementById("id_language_color") as HTMLSelectElement;
    languageColorSelect?.addEventListener("change", renderLanguageColorPreview);
    // Simulate initial input after page load
    languageColorSelect?.dispatchEvent(new Event("change"));
});
