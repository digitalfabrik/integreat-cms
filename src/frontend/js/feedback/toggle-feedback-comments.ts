/*
 * This file provides a simple spoiler for feedback comments with hide/show functionality.
 */

u(".toggle-feedback-comment").on("click", function(event) {
    u(event.target).closest(".feedback-comment").children().each(function(node) {
        u(node).toggleClass("hidden");
    });
});

u("tr").on("click", function(event) {
    if (!u(event.target).is("input") && !u(event.target).is("a") && u(event.target).closest(".toggle-feedback-comment").length === 0) {
        let checkbox = u(event.target).closest("tr").find("input").first();
        checkbox.checked = !checkbox.checked;
    }
});
