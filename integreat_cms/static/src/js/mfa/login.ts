import { getCsrfToken } from "../utils/csrf-token";
import { transformAssertionForServer, transformCredentialRequestOptions } from "../utils/mfa-utils";

// Based on https://github.com/duo-labs/py_webauthn/blob/master/flask_demo/static/js/webauthn.js
window.addEventListener("load", async () => {
    const assertUrlData = document.querySelector("[data-mfa-login]");
    if (!assertUrlData) {
        return;
    }
    try {
        const webauthn_assert = await (await fetch(assertUrlData.getAttribute("data-mfa-login-assert-url"))).json();

        const transformedCredentialRequestOptions = transformCredentialRequestOptions(webauthn_assert);

        // request the authenticator to create an assertion signature using the
        // credential private key
        let assertion = (await navigator.credentials.get({
            publicKey: transformedCredentialRequestOptions,
        })) as PublicKeyCredential;

        // we now have an authentication assertion! encode the byte arrays contained
        // in the assertion data as strings for posting to the server
        const transformedAssertionForServer = transformAssertionForServer(assertion);

        const result = await fetch(assertUrlData.getAttribute("data-mfa-login-verify-url"), {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
                "X-CSRFToken": getCsrfToken(),
            },
            body: JSON.stringify(transformedAssertionForServer),
        });
        const data = await result.json();
        if (data.success) {
            location.href = "/";
        } else {
            document.querySelector(".auth-error").classList.remove("hidden");
            setTimeout(() => (location.href = "/"), 2000);
        }
    } catch (e) {
        console.error(e);
        document.querySelector(".auth-error").classList.remove("hidden");
        setTimeout(() => (location.href = "/"), 2000);
    }
});
