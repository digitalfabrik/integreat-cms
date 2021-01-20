window.addEventListener("load", () => {
    let passwordInput = document.getElementById("id_password") as HTMLInputElement;
    let passwordWrapper = passwordInput?.closest("div");
    let activeInput = document.getElementById("id_is_active") as HTMLInputElement;
    let activeWrapper = activeInput?.closest("div");
    let activationLinkInput = document.getElementById("id_send_activation_link") as HTMLInputElement;
    let activationLinkWrapper = activationLinkInput?.closest("div");

    if (activationLinkInput?.checked){
        passwordWrapper.hidden = true;
        activeWrapper.hidden = true;
    }
    if (activeInput?.checked){
        activationLinkWrapper.hidden = true;
    }
    activationLinkInput?.addEventListener("change", ({ target }) => {
        // Clear previous user input
        passwordInput.value = '';
        passwordInput.required = !activationLinkInput.checked;
        activeInput.checked = false;
        // Disable manual setting of active and password when sending activation link is chosen
        passwordWrapper.hidden = activationLinkInput.checked;
        activeWrapper.hidden = activationLinkInput.checked;
    });
    activeInput?.addEventListener("change", ({ target }) => {
        // Clear previous user input
        if (!activeInput.checked) {
            passwordInput.value = '';
        }
        activationLinkInput.checked = false;
        // Disable manual setting of active and password when sending activation link is chosen
        activationLinkWrapper.hidden = activeInput.checked;
    });
});
