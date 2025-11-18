/**
 * This file adds the class "border-red-500" to the slug div if there is an error in the field
 *
 * used in:
 * event_form.html
 * page_form.html
 * poi_form.html
 *
 */

window.addEventListener("load", () => {
    document
        .querySelectorAll(".slug-error")
        .forEach((node) => node.closest("#slug-div").classList.add("border-red-500"));
});
