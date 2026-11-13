import { describe, expect, test } from "vitest";
import { addMissingUrlScheme } from "../../utils/url";

describe("addMissingUrlScheme", () => {
    test.each([
        ["www.example.com", "https://www.example.com"],
        ["example.com/path?query=1", "https://example.com/path?query=1"],
        ["www.example.com:8080/path", "https://www.example.com:8080/path"],
        ["  www.example.com  ", "https://www.example.com"],
        ["//example.com", "https://example.com"],
    ])("prepends https:// to %j", (input, expected) => {
        expect(addMissingUrlScheme(input, "invalid")).toBe(expected);
    });

    test.each([
        "https://www.example.com",
        "http://www.example.com",
        "HTTPS://www.example.com",
        "mailto:info@example.com",
        "tel:+49821123456",
        "",
        "   ",
    ])("leaves %j unchanged", (input) => {
        expect(addMissingUrlScheme(input,"invalid")).toBe(input);
    });
});
