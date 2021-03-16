import tinymce from "tinymce";

/**
 * This file contains the functionality to copy content from the source to the target translation
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
      const source_translation_tinymce = tinymce.get(
        "source_translation_tinymce"
      );
      const target_translation_tinymce = tinymce.get(
        "target_translation_tinymce"
      );
      target_translation_tinymce.setContent(
        source_translation_tinymce.getContent()
      );
    });
  }
});
