import { describe, expect, test } from "vitest";
import { addMissingUrlScheme } from "../../utils/url";

describe("addMissingUrlScheme", () => {
    test.each([
        ["www.example.com", "https://www.example.com"],
        ["example.com/path?query=1", "https://example.com/path?query=1"],
        ["www.example.com:8080/path", "https://www.example.com:8080/path"],
        ["  www.example.com  ", "https://www.example.com"],
        ["//example.com", "https://example.com"],
        ["192.168.0.1", "https://192.168.0.1"],
        ["example.com/@user", "https://example.com/@user"],
    ])("prepends https:// to %j", (input, expected) => {
        expect(addMissingUrlScheme(input)).toBe(expected);
    });

    test.each([
        ["info@example.com", "mailto:info@example.com"],
        ["  first.last+tag@sub.example.org ", "mailto:first.last+tag@sub.example.org"],
    ])("prepends mailto: to %j", (input, expected) => {
        expect(addMissingUrlScheme(input)).toBe(expected);
    });

    test.each([
        ["+49821123456", "tel:+49821123456"],
        ["+49 821 123456", "tel:+49821123456"],
        ["0821/123456", "tel:0821123456"],
        ["(0821) 123-456", "tel:(0821)123-456"],
    ])("prepends tel: to %j", (input, expected) => {
        expect(addMissingUrlScheme(input)).toBe(expected);
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
        expect(addMissingUrlScheme(input)).toBe(input);
    });
});
