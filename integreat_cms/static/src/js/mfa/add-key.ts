import { getCsrfToken } from "../utils/csrf-token";
import { b64enc, transformCredentialCreateOptions } from "../utils/mfa-utils";

// Based on https://github.com/duo-labs/py_webauthn/blob/master/flask_demo/static/js/webauthn.js
window.addEventListener("load", () => {
    const addMfaForm = document.getElementById("add-mfa-key") as HTMLFormElement;
    if (!addMfaForm) {
        return;
    }
    const nameField = document.getElementById("id_name") as HTMLInputElement;

    if (!navigator.credentials.create) {
        document.querySelector(".add-mfa").classList.add("hidden");
        document.querySelector(".mfa-not-supported").classList.remove("hidden");
    }

    addMfaForm.addEventListener("submit", async (e) => {
        e.preventDefault();
        e.stopPropagation();
        try {
            document.querySelector(".add-mfa-error").classList.add("hidden");
            document.querySelector(".add-mfa-error-msg").textContent = "";
            const response = await fetch(addMfaForm.getAttribute("data-mfa-challenge-url"));
            const webauthnConfiguration = await response.json();

            const newAssertion = (await navigator.credentials.create({
                publicKey: transformCredentialCreateOptions(webauthnConfiguration),
            })) as PublicKeyCredential;

            const attestationObject = new Uint8Array(
                (newAssertion.response as AuthenticatorAttestationResponse).attestationObject
            );
            const clientDataJSON = new Uint8Array(newAssertion.response.clientDataJSON);
            const rawId = new Uint8Array(newAssertion.rawId);

            const formData = {
                id: newAssertion.id,
                rawId: b64enc(rawId),
                type: newAssertion.type,
                response: {
                    attestationObject: b64enc(attestationObject),
                    clientDataJSON: b64enc(clientDataJSON),
                },
                clientExtensionResults: newAssertion.getClientExtensionResults(),
            };

            const result = await fetch(addMfaForm.action, {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                    "X-CSRFToken": getCsrfToken(),
                },
                body: JSON.stringify({
                    ...formData,
                    name: nameField.value,
                }),
            });
            const data = await result.json();
            if (data.success) {
                location.href = data.successUrl;
            } else {
                document.querySelector(".add-mfa-error").classList.remove("hidden");
                document.querySelector(".add-mfa-error-msg").textContent = data.error;
            }
        } catch (e) {
            console.error(e);
            document.querySelector(".add-mfa-error").classList.remove("hidden");
        }
    });
});
