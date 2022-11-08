import { getCookie } from "./cookies";

export function getCsrfToken(): string {
    return getCookie("csrftoken");
}
