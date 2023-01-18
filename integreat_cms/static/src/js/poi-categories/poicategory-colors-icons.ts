const renderColorPreview = ({ target }: Event) => {
    const colorSelect = target as HTMLSelectElement;
    const colorPreview = document.getElementById("poi-category-color-preview");
    const selectedColor = colorSelect.options[colorSelect.selectedIndex].value;
    if (selectedColor) {
        colorPreview.style.backgroundColor = selectedColor;
        colorPreview.classList.remove("hidden");
        colorSelect.classList.add("rounded-none", "rounded-r", "border-l-0");
    } else {
        colorPreview.classList.add("hidden");
        colorSelect.classList.remove("rounded-none", "rounded-r", "border-l-0");
    }
};

const renderIconPreview = ({ target }: Event) => {
    const iconSelect = target as HTMLSelectElement;
    const iconPreview = document.getElementById("poi-category-icon-preview");
    const selectedIcon = iconSelect.options[iconSelect.selectedIndex].value;

    if (selectedIcon) {
        iconPreview.setAttribute("src", `${iconPreview.dataset.basePath}${selectedIcon}.svg`);
        iconPreview.classList.remove("hidden");
    } else {
        iconPreview.classList.add("hidden");
    }
};

const colorizeIcons = () => {
    const icons = document.querySelectorAll(".preview-color:not([data-color=''])") as NodeListOf<HTMLObjectElement>;
    Array.from(icons).forEach((icon) => {
        icon.getSVGDocument().querySelector("circle").setAttribute("fill", icon.dataset.color);
    });
};

window.addEventListener("load", () => {
    // Colorize the icons in the list view
    colorizeIcons();

    const colorSelect = document.getElementById("id_color") as HTMLSelectElement;
    colorSelect?.addEventListener("change", renderColorPreview);
    // Simulate initial input after page load
    colorSelect?.dispatchEvent(new Event("change"));

    const iconSelect = document.getElementById("poi-category-icon-field") as HTMLSelectElement;

    iconSelect?.addEventListener("change", renderIconPreview);
    // Simulate initial input after page load
    iconSelect?.dispatchEvent(new Event("change"));
});
