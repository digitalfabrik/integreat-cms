import tinymce from "tinymce";
import { getCsrfToken } from "../utils/csrf-token";

const formatDate = (date: Date) => {
    const options: Intl.DateTimeFormatOptions = {
        day: "2-digit",
        month: "long",
        year: "numeric",
        hour: "2-digit",
        minute: "2-digit",
    };

    return new Intl.DateTimeFormat(document.documentElement.lang, options).format(date);
};

export const autosaveEditor = async () => {
    const form = document.getElementById("content_form") as HTMLFormElement;
    // Content to be saved
    // Also gets content out of the editor into the text field that was
    // converted to the full editor, but returns it as well.
    // Option format raw for UTF8 and no HTML encoding
    const savingContent = tinymce.activeEditor.save({ source_view: true });

    console.debug(
        savingContent === tinymce.activeEditor.startContent ? "autosave not necessary" : "performing autosave…"
    );

    // Only save if content has changed
    if (savingContent !== tinymce.activeEditor.startContent) {
        document.querySelectorAll("[data-unsaved-warning]").forEach((element) => {
            element.dispatchEvent(new Event("attemptingAutosave"));
        });

        // Prepare the data to send
        const formData = new FormData(form);
        // Override status to "auto save"
        formData.append("status", "AUTO_SAVE");
        // Override minor edit field to keep translation status
        formData.set("minor_edit", "on");
        // Show auto save remark
        const autoSaveNote = document.getElementById("auto-save");
        autoSaveNote.classList.remove("hidden");
        const autoSaveTime = document.getElementById("auto-save-time");
        autoSaveTime.innerText = formatDate(new Date());
        form.addEventListener("input", () => {
            autoSaveNote.classList.add("hidden");
        });
        const data = await fetch(form.action, {
            method: "POST",
            headers: {
                "X-CSRFToken": getCsrfToken(),
            },
            body: formData,
        });
        if (data.ok) {
            // Set the form action to the url of the server response to make sure new pages aren't created multiple times
            form.action = data.url;

            // Set the now successfully saved content as the start content,
            // so that we can always compare whether any changes were made since the last save.
            tinymce.activeEditor.startContent = savingContent;

            // mark the content as saved
            document.querySelectorAll("[data-unsaved-warning]").forEach((element) => {
                element.dispatchEvent(new Event("autosave"));
            });
        } else {
            console.warn("Autosave failed!", data);
        }
    }
};
