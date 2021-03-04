/**
 * This file contains all functions which are needed for the page side by side view dropdown and button.
 */

function toggle_sbs_button({ target }: Event) {
  const sideBySideLink = document.getElementById("side-by-side-link");
  if ((target as HTMLInputElement).value !== "") {
    sideBySideLink.setAttribute("href", (target as HTMLInputElement).value);
    sideBySideLink.classList.remove("bg-gray-400");
    sideBySideLink.classList.remove("pointer-events-none");
    document.getElementById("side-by-side-link").classList.add("bg-blue-500");
    sideBySideLink.classList.add("hover:bg-blue-600");
  } else {
    document.getElementById("side-by-side-link").removeAttribute("href");
    sideBySideLink.classList.remove("bg-blue-500");
    sideBySideLink.classList.remove("hover:bg-blue-600");
    document.getElementById("side-by-side-link").classList.add("bg-gray-400");
    sideBySideLink.classList.add("pointer-events-none");
  }
}
document.addEventListener("DOMContentLoaded", () => {
  const sideBySideSelect = document.getElementById(
    "side-by-side-select"
  ) as HTMLSelectElement;
  if (sideBySideSelect) {
    sideBySideSelect.addEventListener("change", toggle_sbs_button);
    sideBySideSelect.dispatchEvent(new Event("change"));
  }
});
