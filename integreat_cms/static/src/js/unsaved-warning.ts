/**
 * This file contains a function to warn the user when they leave a content without saving
 */

let dirty = false;


window.addEventListener("beforeunload", (event) => {
  // trigger only when something is edited and no submit/save button clicked
  if (dirty) {
    event.preventDefault();
    event.returnValue = "This content is not saved. Would you leave the page?";
  }
});


window.addEventListener("load", () => {
  const form = document.querySelector("[data-unsaved-warning]");
  // checks whether the user typed something in the content
  form?.addEventListener("input", () => {
    if (!dirty) {
      console.debug("editing detected, enabled beforeunload warning");
    }
    dirty = true;
  });
  // checks whether the user has saved or submitted the content
  form?.addEventListener("submit", () => {
    dirty = false;
    console.debug("form submitted, disabled beforeunload warning");
  });
  // removes the warning on autosave
  form?.addEventListener("autosave", () => {
    dirty = false;
    console.debug("Autosave, disabled beforeunload warning");
  })
});
