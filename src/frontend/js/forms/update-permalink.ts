/* this file updates the permalink of the current page form
when the user edited the page translations title */

import { getCsrfToken } from "../utils/csrf-token";

window.addEventListener("load", () => {
  if (
    document.getElementById("id_title") &&
    (document.querySelector('[for="id_title"]') as HTMLElement)?.dataset
      ?.slugifyUrl
  ) {
    document
      .getElementById("id_title")
      .addEventListener("focusout", ({ target }) => {
        const currentTitle = (target as HTMLInputElement).value;
        const url = (document.querySelector('[for="id_title"]') as HTMLElement)
          .dataset.slugifyUrl;
        slugify(url, { title: currentTitle }).then((response) => {
          document
            .getElementById("id_slug")
            .setAttribute("value", response["unique_slug"]);
        });
      });
  }
});

async function slugify(url: string, data: any) {
  const response = await fetch(url, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      HTTP_X_REQUESTED_WITH: "XMLHttpRequest",
      "X-CSRFToken": getCsrfToken(),
    },
    body: JSON.stringify(data),
  }).then((response) => response.json());
  return response;
}
