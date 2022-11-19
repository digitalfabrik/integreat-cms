import HtmlDiff from "htmldiff-js";
import tinymce from "tinymce";

/**
 * This file contains the functionality to copy title and content from the source to the target translation
 * in the page side-by-side view.
 */
window.addEventListener("load", () => {
    const copyTranslation = document.getElementById("copy-translation-content");
    const sourceTinyMce = tinymce.get("source_translation_tinymce");
    if (sourceTinyMce) {
        sourceTinyMce.setMode("readonly");
    }

    if (copyTranslation) {
        copyTranslation.addEventListener("click", (event) => {
            event.preventDefault();
            const sourceTranslationContent = document.getElementById("source_translation_tinymce").dataset.new;
            const targetTranslationTinymce = tinymce.get("target_translation_tinymce");
            targetTranslationTinymce.setContent(sourceTranslationContent);

            const sourceTranslationTitle = document.getElementById("source_translation_title") as HTMLInputElement;
            const targetTranslationTitle = document.getElementById("target_translation_title") as HTMLInputElement;
            targetTranslationTitle.value = sourceTranslationTitle.value;
        });
    }

    // Render diffs
    const sourceEditor = document.getElementById("source_translation_tinymce") as HTMLElement;
    const oldText = sourceEditor?.dataset.old;
    const newText = sourceEditor?.dataset.new;
    if (sourceEditor) {
        sourceEditor.setAttribute("data-diff", HtmlDiff.execute(oldText, newText));
    }

    const toggleButton = document.getElementById("toggle-translation-diff");
    toggleButton?.addEventListener("click", (event) => {
        event.preventDefault();

        // Update Button text
        toggleButton.querySelectorAll(":scope > div").forEach((child) => child.classList.toggle("hidden"));

        const showDiff = !toggleButton.querySelector(".toggle").classList.contains("hidden");
        const editor = tinymce.get("source_translation_tinymce");
        if (showDiff) {
            const diffText = sourceEditor?.dataset.diff;
            editor.setContent(diffText);
        } else {
            const text = sourceEditor?.dataset.new;
            editor.setContent(text);
        }
    });
});
