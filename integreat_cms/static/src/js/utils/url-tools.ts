export function stripProtocol(url: string) {
    return url.replace(/^[^:/]*:\/\//, "");
}
