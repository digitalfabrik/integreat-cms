const enforceMutualExclusion = (clickedCheckbox: HTMLInputElement) => {
    // ignore disabled checkboxes and allow un-checking of all boxes
    if (clickedCheckbox.disabled || !clickedCheckbox.checked) {
        return;
    }
    const checkboxes = <HTMLInputElement[]>(<any>document.querySelectorAll(".mutually-exclusive-checkbox"));
    checkboxes.forEach((checkbox) => {
        if (!checkbox.disabled) {
            // eslint-disable-next-line no-param-reassign
            checkbox.checked = false;
            checkbox.dispatchEvent(new Event("change"));
        }
    });
    // eslint-disable-next-line no-param-reassign
    clickedCheckbox.checked = true;
};

window.addEventListener("load", () => {
    const checkboxes = <HTMLInputElement[]>(<any>document.querySelectorAll(".mutually-exclusive-checkbox"));
    checkboxes.forEach((checkbox) => {
        // eslint-disable-next-line no-param-reassign
        checkbox.addEventListener("click", () => enforceMutualExclusion(checkbox));
    });
});
