import { getCsrfToken } from "../utils/csrf-token";
import { b64enc, transformCredentialCreateOptions } from "../utils/mfa-utils";

// Based on https://github.com/duo-labs/py_webauthn/blob/master/flask_demo/static/js/webauthn.js
window.addEventListener("load", () => {
  const addMfaForm = document.querySelector('form[data-action="add2FaKey"]');
  const nicknameField = document.querySelector(
    'input[name="nickname"]'
  ) as HTMLInputElement;
  if (!addMfaForm || !nicknameField) {
    return;
  }

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
      const webauthnConfiguration = await (
        await fetch("/user_settings/mfa/get_challenge/")
      ).json();

      const newAssertion = (await navigator.credentials.create({
        publicKey: transformCredentialCreateOptions(webauthnConfiguration),
      })) as PublicKeyCredential;

      const attObj = new Uint8Array(
        (newAssertion.response as AuthenticatorAttestationResponse).attestationObject
      );
      const clientDataJSON = new Uint8Array(
        newAssertion.response.clientDataJSON
      );
      const rawId = new Uint8Array(newAssertion.rawId);

      const registrationClientExtensions = newAssertion.getClientExtensionResults();

      const formData = {
        id: newAssertion.id,
        rawId: b64enc(rawId),
        type: newAssertion.type,
        attObj: b64enc(attObj),
        clientData: b64enc(clientDataJSON),
        registrationClientExtensions: JSON.stringify(
          registrationClientExtensions
        ),
      };

      const result = await fetch(document.querySelector("[data-add-mfa-key-url]").getAttribute("data-add-mfa-key-url"), {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "X-CSRFToken": getCsrfToken(),
        },
        body: JSON.stringify({
          assertion: formData,
          nickname: nicknameField.value,
        }),
      });
      const data = await result.json();
      if (data.success) {
        location.href = document.querySelector("[data-mfa-user-settings-url]").getAttribute("data-mfa-user-settings-url");
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
