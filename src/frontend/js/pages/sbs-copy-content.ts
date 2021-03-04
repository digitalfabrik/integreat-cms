/**
 * This file contains the functionality to copy content from the source to the target translation
 * in the page side-by-side view.
 */
u('#copy-translation-content').handle('click', function (event) {
    let source_translation_tinymce = tinymce.get('source_translation_tinymce');
    let target_translation_tinymce = tinymce.get('target_translation_tinymce');
    target_translation_tinymce.setContent(source_translation_tinymce.getContent());
});
