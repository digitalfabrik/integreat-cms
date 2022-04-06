/**
 * This file contains a function to warn the user when they leave a content without saving
 */

let confirmed = false;
let edited = false;


window.addEventListener("beforeunload", (event) => {
  // trigger only when something is edited and no submit/save button clicked
  if (edited && !confirmed) {
    event.preventDefault();
    event.returnValue = "This content is not saved. Would you leave the page?";
  }
});


window.addEventListener("load", () => {
  const form = document.querySelector("[data-unsaved-warning]");
  // checks whether the user typed something in the content
  form?.addEventListener("input", () => {
    edited = true;
    console.debug("editing detected, enabled beforeunload warning");
  }, { once: true });
  // checks whether the user has saved or submitted the content
  form?.addEventListener("submit", () => {
    confirmed = true;
    console.debug("form submitted, disabled beforeunload warning");
  });
});

/**
 * This function marks the form as submitted, so no unsaved warning will be shown
 */
export function markContentSaved() {
  confirmed = true;
}
