import tinymce from "tinymce";
import { getCsrfToken } from "../utils/csrf-token";

export const autosaveEditor = async () => {
    const form = document.getElementById("content_form") as HTMLFormElement;
    tinymce.triggerSave();
    const formData = new FormData(form);
    // Override status to "auto save"
    formData.append("status", "AUTO_SAVE");
    // Override minor edit field to keep translation status
    formData.set("minor_edit", "on");
    const data = await fetch(form.action, {
        method: "POST",
        headers: {
            "X-CSRFToken": getCsrfToken(),
        },
        body: formData,
    });
    // Set the form action to the url of the server response to make sure new pages aren't created multiple times
    form.action = data.url;

    // mark the content as saved
    document.querySelectorAll("[data-unsaved-warning]").forEach((element) => {
        element.dispatchEvent(new Event("autosave"));
    });
};
