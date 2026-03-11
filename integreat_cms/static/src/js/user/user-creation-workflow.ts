window.addEventListener("load", () => {
    const passwordInput = document.getElementById("id_password") as HTMLInputElement;
    const passwordWrapper = passwordInput?.closest("div");
    const activeInput = document.getElementById("id_is_active") as HTMLInputElement;
    const activeWrapper = activeInput?.closest("div");
    const activationLinkInput = document.getElementById("id_send_activation_link") as HTMLInputElement;
    const activationLinkWrapper = activationLinkInput?.closest("div");

    if (activationLinkInput?.checked) {
        passwordWrapper.hidden = true;
        activeWrapper.hidden = true;
    }
    if (activeInput?.checked && activationLinkWrapper) {
        activationLinkWrapper.hidden = true;
    }
    activationLinkInput?.addEventListener("change", () => {
        // Clear previous user input
        passwordInput.value = "";
        passwordInput.required = !activationLinkInput.checked;
        activeInput.checked = false;
        // Disable manual setting of active and password when sending activation link is chosen
        passwordWrapper.hidden = activationLinkInput.checked;
        activeWrapper.hidden = activationLinkInput.checked;
    });
    activeInput?.addEventListener("change", () => {
        // Clear previous user input
        if (!activeInput.checked) {
            passwordInput.value = "";
        }
        activationLinkInput.checked = false;
        if (activationLinkWrapper) {
            // Disable manual setting of active and password when sending activation link is chosen
            activationLinkWrapper.hidden = activeInput.checked;
        }
    });
});
