import base64js from "base64-js";

type CredentialDescriptor = {
    type: string;
    id: string;
    transport: string;
};

type WebauthnAssert = {
    challenge: string;
    allowCredentials: CredentialDescriptor[];
};

type CredentialResponseFromServer = {
    pubKeyCredParams: PublicKeyCredentialParameters[];
    rp: PublicKeyCredentialRpEntity;
    challenge: string;
    user: {
        id: string;
        name: string;
        displayName: string;
    };
};

// Based on https://github.com/MasterKale/SimpleWebAuthn/blob/master/packages/browser/src/helpers/bufferToBase64URLString.ts
export const b64enc = (buf: Uint8Array) =>
    base64js.fromByteArray(buf).replace(/\+/g, "-").replace(/\//g, "_").replace(/=/g, "");

// Based on https://github.com/MasterKale/SimpleWebAuthn/blob/master/packages/browser/src/helpers/base64URLStringToBuffer.ts
const b64dec = (b64url: string) =>
    Uint8Array.from(atob(b64url.replace(/-/g, "+").replace(/_/g, "/")), (c) => c.charCodeAt(0));

const b64RawEnc = (buf: Uint8Array) => base64js.fromByteArray(buf).replace(/\+/g, "-").replace(/\//g, "_");

export const transformCredentialRequestOptions = (
    credentialRequestOptionsFromServer: WebauthnAssert
): PublicKeyCredentialRequestOptions => {
    const { challenge } = credentialRequestOptionsFromServer;
    const challengeData = Uint8Array.from(atob(challenge.replace(/-/g, "+").replace(/_/g, "/")), (c) =>
        c.charCodeAt(0)
    );

    const allowCredentials = credentialRequestOptionsFromServer.allowCredentials.map((credentialDescriptor) => {
        let { id } = credentialDescriptor;
        id = id.replace(/_/g, "/").replace(/-/g, "+");
        const idData = Uint8Array.from(atob(id), (c) => c.charCodeAt(0));
        const result = { ...credentialDescriptor, id: idData };
        return result as PublicKeyCredentialDescriptor;
    });

    const transformedCredentialRequestOptions = {
        ...credentialRequestOptionsFromServer,
        challenge: challengeData,
        allowCredentials,
    };

    return transformedCredentialRequestOptions;
};

export const transformAssertionForServer = (newAssertion: PublicKeyCredential) => {
    const response = newAssertion.response as AuthenticatorAssertionResponse;
    const authenticatorData = new Uint8Array(response.authenticatorData);
    const clientDataJSON = new Uint8Array(response.clientDataJSON);
    const userHandle = new Uint8Array(response.userHandle);

    const rawId = new Uint8Array(newAssertion.rawId);
    const sig = new Uint8Array(response.signature);
    const assertionClientExtensions = newAssertion.getClientExtensionResults();

    return {
        id: newAssertion.id,
        rawId: b64enc(rawId),
        type: newAssertion.type,
        response: {
            authenticatorData: b64RawEnc(authenticatorData),
            clientDataJSON: b64RawEnc(clientDataJSON),
            signature: b64RawEnc(sig),
            userHandle: b64RawEnc(userHandle),
        },
        assertionClientExtensions: JSON.stringify(assertionClientExtensions),
    };
};

export const transformCredentialCreateOptions = (credentialCreateOptionsFromServer: CredentialResponseFromServer) => {
    const { challenge, user } = credentialCreateOptionsFromServer;

    const userIdData = b64dec(user.id);
    const challengeData = b64dec(challenge);

    const transformedCredentialCreateOptions = {
        ...credentialCreateOptionsFromServer,
        challenge: challengeData,
        user: { ...user, id: userIdData },
    };

    return transformedCredentialCreateOptions;
};
