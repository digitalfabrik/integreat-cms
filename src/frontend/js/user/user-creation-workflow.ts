window.addEventListener("load", () => {
    var passwordInput = <HTMLInputElement>document.getElementById("id_password");
    var activeInput = <HTMLInputElement>document.getElementById("id_is_active");
    var activationLinkInput = <HTMLInputElement>document.getElementById("id_send_activation_link");
    var passwordWrapper = passwordInput?.closest("div");
    var activeWrapper = activeInput?.closest("div");
    if (activationLinkInput?.checked){
        passwordWrapper.classList.add("hidden");
        activeWrapper.classList.add("hidden");
    }
    document
        .getElementById("id_send_activation_link")
        ?.addEventListener("change", (event) => {
            // clear pervious user input
            passwordInput.value = '';
            activeInput.checked = false;
            // disable manual setting of active and password
            // when sending activation link is choosen
            passwordWrapper.classList.toggle("hidden");
            activeWrapper.classList.toggle("hidden");
    });
});
