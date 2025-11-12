window.addEventListener("load", () => {
    const activeButton = document.getElementById("id_active");
    if (activeButton) {
        activeButton.addEventListener("change", (event) => {
            const activeCheckbox = event.target as HTMLInputElement;
            const visibleCheckbox = document.getElementById("id_visible") as HTMLInputElement;
            const warningDiv = document.getElementById("visible-warning") as HTMLDivElement;
            if (!activeCheckbox.checked) {
                if (visibleCheckbox.checked) {
                    warningDiv.classList.toggle("hidden", false);
                }
                visibleCheckbox.disabled = true;
                visibleCheckbox.checked = false;
            } else {
                visibleCheckbox.disabled = false;
                warningDiv.classList.toggle("hidden", true);
            }
        });
    }
});
