/**
 * Generate a page preview pop-up.
 * Put the form handling in a separate file because it interacts
 * with the TinyMCE components which can only be initialized once.
 */
import { getContent } from "../forms/tinymce-init";
import { addPreviewWindowListeners } from "./page-preview";


window.addEventListener("load", () => {
  addPreviewWindowListeners(openPreviewWindowInPageForm);
});


async function openPreviewWindowInPageForm(overlay: HTMLElement, btn: Element) {
  const rightToLeft = btn.getAttribute("data-right-to-left") == "True";
  const title = (document.getElementById("id_title") as HTMLInputElement)?.value;
  const pageContent = getContent();
  // If the language is read from right to left, change the text layout to align right.
  rightToLeft ? overlay.classList.add("text-right") : overlay.classList.remove("text-right");
  // Insert title and page content.
  document.getElementById("preview-content-header").textContent = title;
  document.getElementById("preview-content-block").innerHTML = pageContent;
  const firstBlock = document.getElementById("preview-content-block-first");
  const lastBlock = document.getElementById("preview-content-block-last");
  // Reset mirrored page blocks
  firstBlock.innerHTML = "";
  lastBlock.innerHTML = "";
  // Get currently selected mirrored page
  const mirroredPageField = document.getElementById("mirrored_page") as HTMLInputElement;
  if (mirroredPageField) {
    const mirroredPageId = mirroredPageField.value;
    // Get selected option node
    const selectedOption = mirroredPageField.querySelector('option[value="' + mirroredPageId + '"]');
    // fetch mirrored page content based on the current dropdown value states.
    const mirroredPagePreviewUrl = selectedOption?.getAttribute("data-preview-url");
    if (mirroredPagePreviewUrl) {
      const mirroredPageContent = await fetch(mirroredPagePreviewUrl)
        .then((response) => response.json())
        .then((data) => {
          return data["content"];
        });
      const mirroredPageFirst =
        (document.getElementById("mirrored_page_first") as HTMLInputElement)?.value === "True";
      // Insert mirrored page content before or after page content.
      if (mirroredPageFirst) {
        firstBlock.innerHTML = mirroredPageContent;
        lastBlock.innerHTML = "";
      } else {
        firstBlock.innerHTML = "";
        lastBlock.innerHTML = mirroredPageContent;
      }
    }
  }
  overlay.classList.remove("hidden");
  overlay.classList.add("flex");
}
