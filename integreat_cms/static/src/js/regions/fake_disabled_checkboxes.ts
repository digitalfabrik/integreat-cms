window.addEventListener("load", () => {
    const checkboxes = <HTMLInputElement[]>(<any>document.querySelectorAll(".fake-disable-region"));
    checkboxes.forEach((checkbox) => {
        const label = document.querySelector(`label[for='${checkbox.id}']`);
        label.classList.add("pointer-events-none");
    });
});
