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
      const source_translation_content = document.getElementById("source_translation_tinymce").dataset.new;
      const target_translation_tinymce = tinymce.get(
        "target_translation_tinymce"
      );
      target_translation_tinymce.setContent(source_translation_content);

      const source_translation_title = document.getElementById("source_translation_title") as HTMLInputElement;
      const target_translation_title = document.getElementById("target_translation_title") as HTMLInputElement;
      target_translation_title.value = source_translation_title.value;
    });
  }

  // Render diffs
  const source_editor = document.getElementById("source_translation_tinymce") as HTMLElement
  const oldText = source_editor?.dataset.old;
  const newText = source_editor?.dataset.new;
  if (source_editor) {
    source_editor.setAttribute("data-diff", HtmlDiff.execute(oldText, newText));
  }

  const toggleButton = document.getElementById("toggle-translation-diff");
  toggleButton?.addEventListener("click", (event) => {
    event.preventDefault();

    // Update Button text
    toggleButton.querySelectorAll(":scope > div").forEach((child) => child.classList.toggle("hidden"));

    const show_diff = !toggleButton.querySelector(".toggle").classList.contains("hidden");
    const editor = tinymce.get("source_translation_tinymce");
    if (show_diff) {
      const diffText = source_editor?.dataset.diff;
      editor.setContent(diffText);
    } else {
      const text = source_editor?.dataset.new;
      editor.setContent(text);
    }
  })
});
