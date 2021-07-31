import { getCsrfToken } from "../utils/csrf-token";
import tinymce from "tinymce";

export async function autosaveEditor() {
  const form = document.getElementById("content_form") as HTMLFormElement;
  tinymce.triggerSave();
  let formData = new FormData(form);
  formData.append("submit_auto", "true");
  const data = await fetch(form.action, {
    method: "POST",
    headers: {
      "X-CSRFToken": getCsrfToken(),
    },
    body: formData
  });
  // Set the form action to the url of the server response to make sure new pages aren't created multiple times
  form.action = data.url;
}
