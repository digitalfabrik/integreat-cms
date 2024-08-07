import { expect, test } from "vitest";
import { b64enc } from "../../utils/mfa-utils";

test("base64 and url encoding", () => {
    const testDataString = "https://example.com/?q=Hello+World!";
    const testData = new TextEncoder().encode(testDataString);

    expect(b64enc(testData)).toBe("aHR0cHM6Ly9leGFtcGxlLmNvbS8_cT1IZWxsbytXb3JsZCE");
});
