import { getCookie } from "./cookies";

export const getCsrfToken = (): string => getCookie("csrftoken");
