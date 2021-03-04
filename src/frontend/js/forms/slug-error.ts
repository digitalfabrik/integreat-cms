/**
 * This file adds the class "border-red-500" to the slug div if there is an error in the field
 */

window.addEventListener("load", () => {
  document
    .querySelectorAll(".slug-error")
    .forEach((node) =>
      node.closest("#slug-div").classList.add("border-red-500")
    );
});
