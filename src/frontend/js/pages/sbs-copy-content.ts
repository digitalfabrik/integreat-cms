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
      const source_translation_tinymce = tinymce.get(
        "source_translation_tinymce"
      );
      const target_translation_tinymce = tinymce.get(
        "target_translation_tinymce"
      );
      target_translation_tinymce.setContent(
        source_translation_tinymce.getContent()
      );

      const source_translation_title = document.getElementById("source_translation_title") as HTMLInputElement;
      const target_translation_title = document.getElementById("target_translation_title") as HTMLInputElement;
      target_translation_title.value = source_translation_title.value;
    });
  }
});
