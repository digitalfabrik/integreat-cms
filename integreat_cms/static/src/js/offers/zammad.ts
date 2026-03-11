window.addEventListener("load", () => {
    const zammadCheckbox = document.querySelector("#id_is_zammad_form") as HTMLInputElement;
    const urlField = document.querySelector("#id_url") as HTMLInputElement;
    const thumbnailField = document.querySelector("#id_thumbnail") as HTMLInputElement;

    if (!zammadCheckbox || !urlField || !thumbnailField) {
        return;
    }

    zammadCheckbox.addEventListener("change", () => {
        urlField.required = !zammadCheckbox.checked;
        thumbnailField.required = !zammadCheckbox.checked;
    });

    zammadCheckbox.dispatchEvent(new Event("change"));
});

window.addEventListener("load", () => {
    const zammadUrlField = document.querySelector("#id_zammad_url") as HTMLInputElement;
    const zammadOffersWrapper = document.querySelector("#zammad-offers-wrapper") as HTMLElement;

    if (!zammadUrlField || !zammadOffersWrapper) {
        return;
    }

    zammadUrlField.addEventListener("change", () => {
        if (zammadUrlField.value) {
            zammadOffersWrapper.classList.remove("hidden");
        } else {
            zammadOffersWrapper.classList.add("hidden");
        }
    });

    zammadUrlField.dispatchEvent(new Event("change"));
});
