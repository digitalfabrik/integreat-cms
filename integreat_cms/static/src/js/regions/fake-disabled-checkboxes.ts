const setZammadUrlDisabledState = (zammadWrapper: HTMLElement, zammadUrl: HTMLInputElement) => {
    const checkboxes = zammadWrapper.querySelectorAll('input[type="checkbox"].fake-disable-region');
    if (checkboxes.length) {
        zammadUrl.classList.add("pointer-events-none");
    } else {
        zammadUrl.classList.remove("pointer-events-none");
    }
};

window.addEventListener("load", () => {
    const checkboxes = <HTMLInputElement[]>(<any>document.querySelectorAll(".fake-disable-region"));
    checkboxes.forEach((checkbox) => {
        const label = document.querySelector(`label[for='${checkbox.id}']`);
        label.classList.add("pointer-events-none");
    });

    const zammadWrapper = document.querySelector("#zammad-offers-wrapper") as HTMLElement;
    const zammadUrl = document.querySelector("#id_zammad_url") as HTMLInputElement;
    if (!zammadWrapper || !zammadUrl) {
        return;
    }

    const zammadCheckboxes = <HTMLInputElement[]>(<any>zammadWrapper.querySelectorAll('input[type="checkbox"]'));
    zammadCheckboxes.forEach((checkbox) => {
        checkbox.addEventListener("change", () => setZammadUrlDisabledState(zammadWrapper, zammadUrl));
    });
    setZammadUrlDisabledState(zammadWrapper, zammadUrl);
});
