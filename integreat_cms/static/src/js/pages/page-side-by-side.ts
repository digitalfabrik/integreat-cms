/**
 * This file contains all functions which are needed for the page side by side view dropdown and button.
 */

function toggle_sbs_button({ target }: Event) {
  const link_target = (target as HTMLInputElement).value;
  const sideBySideLink = document.getElementById("side-by-side-link") as HTMLLinkElement;
  if (link_target !== "") {
    sideBySideLink.setAttribute("href", encodeURI(link_target));
    sideBySideLink.removeAttribute("disabled");
  } else {
    sideBySideLink.removeAttribute("href");
    sideBySideLink.setAttribute("disabled", "disabled");
  }
}
document.addEventListener("DOMContentLoaded", () => {
  const sideBySideSelect = document.getElementById(
    "side-by-side-select"
  ) as HTMLSelectElement;
  sideBySideSelect?.addEventListener("change", toggle_sbs_button);
  sideBySideSelect?.dispatchEvent(new Event("change"));
});
