import { getCsrfToken } from "../utils/csrf-token";

export async function autosaveEditor() {
  const form = document.getElementById("content_form") as HTMLFormElement;
  const formData = new FormData(form);
  const data = await fetch(window.location.href, {
    method: "POST",
    headers: {
      "X-CSRFToken": getCsrfToken(),
    },
    body: formData
  });
}
