/* this file updates the permalink of the current page form
when the user edited the page translations title 
or when the user clicks the permalinks edit button */

import { getCsrfToken } from "../utils/csrf-token";
import { copyToClipboard } from "../copy-clipboard";

window.addEventListener("load", () => {
  /* slug field buffer for restoring input value */
  var currentSlug: string;
  /* slug field to be updated */
  var slugField = <HTMLInputElement>document.getElementById("id_slug");
  var linkContainer = document.getElementById("link-container");

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
          /* on success write response to both slug field and permalink */
          slugField.value = response["unique_slug"];
          updatePermalink(response["unique_slug"]);
        });
      });
  }


  function toggleSlugMode(){
    // toggle all permalink buttons
    let buttonList = document.getElementById("link-container").querySelectorAll("button");
    for (let button of buttonList) {
      button.classList.toggle("hidden");
    }
    // switch between link and slug field
    linkContainer.querySelector("a").classList.toggle("hidden");
    linkContainer.querySelector("div").classList.toggle("hidden");
  }


  function updatePermalink(currentSlug: string){
    // get complete permalink string
    let currentLink = linkContainer.querySelector("a").textContent;
    // remove trailing slug from link
    let updatedLink = currentLink.substr(0, currentLink.lastIndexOf("/")+1);
    // update only inner html and keep href until form submission
    linkContainer.querySelector("a").textContent = updatedLink.concat(currentSlug);
  }

  document.getElementById("edit-slug-btn")?.addEventListener("click", function(e){
    // buffer the current slug field and toggle to editable
    currentSlug = slugField.value;
    toggleSlugMode();
  });


  document.getElementById("save-slug-btn")?.addEventListener("click", function(e){
    updatePermalink(slugField.value);
    toggleSlugMode();
  });


  document.getElementById("copy-slug-btn")?.addEventListener("click", function(e){
    // copy whole permalink to clipboard
    copyToClipboard(linkContainer.querySelector("a").textContent);
  });


  document.getElementById("restore-slug-btn")?.addEventListener("click", function(e){
    // hide slug field and restore slug value
    slugField.value = currentSlug;
    toggleSlugMode();
  });
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
