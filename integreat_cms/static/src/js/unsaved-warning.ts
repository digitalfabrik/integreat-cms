/**
 * This file contains a function to warn the user when they leave a content without saving
 */
import { editors, isActuallyDirty } from "./forms/tinymce-init";

const takeFormSnapshot = (form: HTMLFormElement) => new FormData(form);

const equalSnapshots = (a: FormData, b: FormData) => {
    // We could inplement a proper comparison of nested arrays
    // …ooor we could just take the hit and stringify everything
    // to JSON, saving us maintenance on all these code lines
    if (a == null || b == null) {
        return false;
    }
    const withoutExcluded = (iterator: IterableIterator<[string, FormDataEntryValue]>) =>
        Array.from(iterator).filter((item) => {
            const target = document.querySelector(`[name="${item[0]}"]`);
            return !target.hasAttribute("data-unsaved-warning-exclude");
        });
    const aJSON = JSON.stringify(withoutExcluded(a.entries()));
    const bJSON = JSON.stringify(withoutExcluded(b.entries()));
    return aJSON === bJSON;
};

const originalTitle = document.title;

let snapshotCandidate: FormData | null = null;
let savedSnapshot: FormData | null = null;

const isDirty = (form: HTMLFormElement) => {
    const now = takeFormSnapshot(form);
    if (!Array.from(now.entries()).length) {
        console.warn("form snapshot has no entries:", now.entries(), form);
    }
    if (!equalSnapshots(now, savedSnapshot)) {
        return true;
    }
    // Are there any unsaved changes in the editors?
    for (const editor of editors) {
        if (isActuallyDirty(editor)) {
            return true;
        }
    }
    return false;
};

// Only temporarily add a beforeunload event
// https://developer.chrome.com/articles/page-lifecycle-api/#the-beforeunload-event
const beforeunload = (event: BeforeUnloadEvent) => {
    console.debug("[beforeunload]");
    event.preventDefault();
    /* eslint-disable-next-line no-param-reassign */
    event.returnValue = "This content is not saved. Would you leave the page?";
    return event.returnValue;
};

const updateState = (form: HTMLFormElement) => {
    // Add/remove beforeunload listener and add an unsaved indicator to the title
    if (isDirty(form)) {
        window.addEventListener("beforeunload", beforeunload);
        document.title = `• ${originalTitle}`;
    } else {
        window.removeEventListener("beforeunload", beforeunload);
        document.title = originalTitle;
    }
};

window.addEventListener("load", () => {
    const form = document.querySelector("[data-unsaved-warning]") as HTMLFormElement;

    // Remember the state on initialization as saved
    savedSnapshot = takeFormSnapshot(form);

    editors.forEach((editor) => {
        const target = editor.targetElm as HTMLInputElement;
        if (target.form === form) {
            editor.on("input", () => {
                updateState(form);
            });
        }
    });

    // checks whether the user typed something in the content
    form?.addEventListener("input", () => {
        updateState(form);
    });

    form?.addEventListener("formdata", (event) => {
        // ensure form has latest tinymce state
        for (const editor of editors) {
            const name = (editor.targetElm as HTMLFormElement).name;
            const content = editor.getContent({ source_view: true });
            event.formData.set(name, content);
        }
    });
    // checks whether the user has saved or submitted the content
    form?.addEventListener("submit", () => {
        window.removeEventListener("beforeunload", beforeunload);
    });
    // take snapshot when attempting autosave
    form?.addEventListener("attemptingAutosave", () => {
        snapshotCandidate = takeFormSnapshot(form);
    });
    // removes the warning on autosave
    form?.addEventListener("autosave", () => {
        savedSnapshot = snapshotCandidate;
        updateState(form);
    });
});
