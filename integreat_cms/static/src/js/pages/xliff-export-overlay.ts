window.addEventListener("load", () => {
    addXliffExportOverlayListeners();
    // Set listener for select toggles.
    document.querySelectorAll(".bulk-select-language").forEach((el) => {
        el.addEventListener("change", toggleXliffBulkActionButton);
    });
    // Set listener for select-all toggle.
    document.getElementById("select-all-languages")?.addEventListener("change", (toggle) => {
        document.querySelectorAll(".bulk-select-language").forEach((el) => {
            (el as HTMLInputElement).checked = (toggle.target as HTMLInputElement).checked;
            toggleXliffBulkActionButton();
        });
    });
});

function addXliffExportOverlayListeners() {
    const overlay = document.getElementById("xliff_export_overlay");
    if (overlay) {
        // Set listener for bulk action execute button.
        document.getElementById("bulk-action-execute")?.addEventListener("click", (event) => {
            const xliffOptionIndex = (document.getElementById("xliff-multiple-languages-option") as HTMLOptionElement)
                .index;
            const selectedIndex = (document.getElementById("bulk-action") as HTMLSelectElement).selectedIndex;
            if (xliffOptionIndex === selectedIndex) {
                event.preventDefault();
                overlay.classList.remove("hidden");
                overlay.classList.add("flex");
            }
        });
        document.getElementById("btn-close-xliff-export").addEventListener("click", () => {
            closeXliffExportOverlay(overlay);
        });
        // Close window by clicking on backdrop.
        overlay.addEventListener("click", (e) => {
            if (e.target === overlay) {
                closeXliffExportOverlay(overlay);
            }
        });
    }
}

function closeXliffExportOverlay(overlay: HTMLElement) {
    overlay.classList.add("hidden");
    overlay.classList.remove("flex");
    toggleXliffBulkActionButton();
}

function toggleXliffBulkActionButton() {
    // Only activate button if at least one language item is selected
    const selectLanguages = <HTMLInputElement[]>Array.from(document.getElementsByClassName("bulk-select-language"));
    const multiLanguageXliffButton = document.getElementById("xliff-overlay-bulk-action-execute") as HTMLButtonElement;
    multiLanguageXliffButton.disabled = !selectLanguages.some((el) => el.checked);
}
