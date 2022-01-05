import base64js from "base64-js";

interface CredentialDescriptor {
  type: string;
  id: string;
  transport: string;
}

interface WebauthnAssert {
  challenge: string;
  allowCredentials: CredentialDescriptor[];
}

interface CredentialResponseFromServer {
  pubKeyCredParams: PublicKeyCredentialParameters[];
  rp: PublicKeyCredentialRpEntity;
  challenge: string;
  user: {
    id: string;
    name: string;
    displayName: string;
  };
}

// Based on https://github.com/duo-labs/py_webauthn/blob/master/flask_demo/static/js/webauthn.js
export function b64enc(buf: Uint8Array) {
  return base64js
    .fromByteArray(buf)
    .replace(/\+/g, "-")
    .replace(/\//g, "_")
    .replace(/=/g, "");
}

function b64RawEnc(buf: Uint8Array) {
  return base64js.fromByteArray(buf).replace(/\+/g, "-").replace(/\//g, "_");
}

function hexEncode(buf: Uint8Array) {
  return Array.from(buf)
    .map(function (x) {
      return ("0" + x.toString(16)).substr(-2);
    })
    .join("");
}

export function transformCredentialRequestOptions(
  credentialRequestOptionsFromServer: WebauthnAssert
): PublicKeyCredentialRequestOptions {
  let { challenge } = credentialRequestOptionsFromServer;
  let challengeData = Uint8Array.from(atob(challenge), (c) => c.charCodeAt(0));

  const allowCredentials = credentialRequestOptionsFromServer.allowCredentials.map(
    (credentialDescriptor) => {
      let { id } = credentialDescriptor;
      id = id.replace(/\_/g, "/").replace(/\-/g, "+");
      const idData = Uint8Array.from(atob(id), (c) => c.charCodeAt(0));
      const result = Object.assign({}, credentialDescriptor, { id: idData });
      return result as PublicKeyCredentialDescriptor;
    }
  );

  const transformedCredentialRequestOptions = Object.assign(
    {},
    credentialRequestOptionsFromServer,
    { challenge: challengeData, allowCredentials }
  );

  return transformedCredentialRequestOptions;
}

export function transformAssertionForServer(newAssertion: PublicKeyCredential) {
  const response = newAssertion.response as AuthenticatorAssertionResponse;
  const authData = new Uint8Array(response.authenticatorData);
  const clientDataJSON = new Uint8Array(response.clientDataJSON);
  const rawId = new Uint8Array(newAssertion.rawId);
  const sig = new Uint8Array(response.signature);
  const assertionClientExtensions = newAssertion.getClientExtensionResults();

  return {
    id: newAssertion.id,
    rawId: b64enc(rawId),
    type: newAssertion.type,
    authData: b64RawEnc(authData),
    clientData: b64RawEnc(clientDataJSON),
    signature: hexEncode(sig),
    assertionClientExtensions: JSON.stringify(assertionClientExtensions),
  };
}

export function transformCredentialCreateOptions(
  credentialCreateOptionsFromServer: CredentialResponseFromServer
) {
  const { challenge, user } = credentialCreateOptionsFromServer;
  const userIdData = Uint8Array.from(
    credentialCreateOptionsFromServer.user.id,
    (c) => c.charCodeAt(0)
  );

  const challengeData = Uint8Array.from(challenge, (c) =>
    c.charCodeAt(0)
  );

  const transformedCredentialCreateOptions = Object.assign(
    {},
    credentialCreateOptionsFromServer,
    { challenge: challengeData, user: { ...user, id: userIdData } }
  );

  transformedCredentialCreateOptions.rp.id = transformedCredentialCreateOptions.rp.id.replace(':8000', '')
  console.log(transformedCredentialCreateOptions)

  return transformedCredentialCreateOptions;
}
