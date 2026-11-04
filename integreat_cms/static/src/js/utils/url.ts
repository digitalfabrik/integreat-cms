/**
 * Matches values which already start with a URL scheme, e.g. "https:", "mailto:" or "tel:".
 * Dots are deliberately not allowed in the scheme, so that a host with a port
 * (e.g. "www.example.com:8080") is not mistaken for a scheme.
 */
const SCHEME_REGEX = /^[a-z][a-z0-9+-]*:/i;

/**
 * Matches values which look like an email address, e.g. "info@example.com".
 */
const EMAIL_REGEX = /^[^\s@/:]+@[^\s@/:]+\.[^\s@/:]+$/;

/**
 * Matches values which look like a phone number, e.g. "+49 821 123456", "(0821) 123-456" or "0821/123456".
 * Dots are deliberately not allowed, so that IP addresses are not mistaken for phone numbers.
 */
const PHONE_REGEX = /^\+?[\d\s()/-]+$/;
const MIN_PHONE_DIGITS = 3;

const isPhoneNumber = (value: string): boolean =>
    PHONE_REGEX.test(value) && (value.match(/\d/g) ?? []).length >= MIN_PHONE_DIGITS;

/**
 * Prepend a scheme to a URL if it does not contain one yet. The scheme is chosen based on the value:
 * - email addresses get "mailto:", e.g. "info@example.com" becomes "mailto:info@example.com"
 * - phone numbers get "tel:", e.g. "+49 821 123456" becomes "tel:+49821123456"
 * - everything else gets "https://", e.g. "www.example.com" becomes "https://www.example.com"
 *
 * @param value The URL entered by the user
 * @returns The URL including a scheme
 */
export const addMissingUrlScheme = (value: string): string => {
    const trimmedValue = value.trim();
    if (!trimmedValue || SCHEME_REGEX.test(trimmedValue)) {
        return value;
    }
    if (EMAIL_REGEX.test(trimmedValue)) {
        return `mailto:${trimmedValue}`;
    }
    if (isPhoneNumber(trimmedValue)) {
        // Whitespace and slashes are not valid visual separators in tel: URIs (RFC 3966)
        return `tel:${trimmedValue.replace(/[\s/]/g, "")}`;
    }
    if (trimmedValue.startsWith("//")) {
        return `https:${trimmedValue}`;
    }
    return `https://${trimmedValue}`;
};
