/*
 * This file provides a simple spoiler for feedback comments with hide/show functionality.
 */
window.addEventListener('load', () => {
    document.querySelectorAll(".toggle-feedback-comment").forEach(toggle => toggle.addEventListener('click', ({target}) => {
        [...(target as HTMLElement).closest(".feedback-comment").children].forEach((node) => {
            (node as HTMLElement).classList.toggle("hidden");
        });
    }));
});
