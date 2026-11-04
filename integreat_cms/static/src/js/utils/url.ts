/**
 * Matches values which already start with a URL scheme, e.g. "https:", "mailto:" or "tel:".
 * Dots are deliberately not allowed in the scheme, so that a host with a port
 * (e.g. "www.example.com:8080") is not mistaken for a scheme.
 */
const SCHEME_REGEX = /^[a-z][a-z0-9+-]*:/i;

/**
 * Prepend "https://" to a URL if it does not contain a scheme yet,
 * e.g. "www.example.com" becomes "https://www.example.com".
 *
 * @param value The URL entered by the user
 * @returns The URL including a scheme
 */
export const addMissingUrlScheme = (value: string): string => {
    const trimmedValue = value.trim();
    if (!trimmedValue || SCHEME_REGEX.test(trimmedValue)) {
        return value;
    }
    if (trimmedValue.startsWith("//")) {
        return `https:${trimmedValue}`;
    }
    return `https://${trimmedValue}`;
};
