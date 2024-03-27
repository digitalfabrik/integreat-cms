/* this file updates the permalink of the current page form
when the user edited the page translations title
or when the user clicks the permalinks edit button */

import { getCsrfToken } from "../utils/csrf-token";
import { copyToClipboard } from "../copy-clipboard";
import SubmissionPrevention from "./prevent-premature-submission";

const slugify = async (url: string, data: any) => {
    const response = await fetch(url, {
        method: "POST",
        headers: {
            "Content-Type": "application/json",
            "HTTP_X_REQUESTED_WITH": "XMLHttpRequest",
            "X-CSRFToken": getCsrfToken(),
        },
        body: JSON.stringify(data),
    }).then((response) => response.json());
    return response;
};

window.addEventListener("load", () => {
    /* slug field buffer for restoring input value */
    let currentSlug: string;
    /* slug field to be updated */
    const slugField = <HTMLInputElement>document.getElementById("id_slug");
    const linkContainer = document.getElementById("link-container");

    const updatePermalink = (currentSlug: string) => {
        // get complete permalink string
        const linkElement = document.getElementById("slug-link");
        const currentLink = linkElement.textContent;
        // remove trailing slug from link
        const updatedLink = currentLink.substr(0, currentLink.lastIndexOf("/") + 1);
        // update only inner html and keep href until form submission
        linkElement.textContent = updatedLink.concat(currentSlug);

        document
            .getElementById("copy-slug-btn")
            .setAttribute("data-copy-to-clipboard", encodeURI(updatedLink.concat(currentSlug)));
    };

    if (
        document.getElementById("id_title") &&
        (document.querySelector('[for="id_title"]') as HTMLElement)?.dataset?.slugifyUrl
    ) {
        document.getElementById("id_title").addEventListener("focusout", ({ target }) => {
            const submissionLock = new SubmissionPrevention(".no-premature-submission");
            const currentTitle = (target as HTMLInputElement).value;
            const url = (document.querySelector('[for="id_title"]') as HTMLElement).dataset.slugifyUrl;
            slugify(url, { title: currentTitle }).then((response) => {
                /* on success write response to both slug field and permalink */
                slugField.value = response.unique_slug;
                updatePermalink(response.unique_slug);
                submissionLock.release();
            });
        });
    }

    const toggleSlugMode = () => {
        // Toggle all permalink buttons (and the rendered link)
        linkContainer.querySelectorAll("a").forEach((link) => link.classList.toggle("hidden"));
        // Toggle slug field
        linkContainer.querySelector("div").classList.toggle("hidden");
    };

    document.getElementById("edit-slug-btn")?.addEventListener("click", (_) => {
        // buffer the current slug field and toggle to editable
        currentSlug = slugField.value;
        toggleSlugMode();
    });

    document.getElementById("save-slug-btn")?.addEventListener("click", (_) => {
        updatePermalink(slugField.value);
        toggleSlugMode();
    });

    document.getElementById("copy-slug-btn")?.addEventListener("click", (_) => {
        // copy whole permalink to clipboard
        copyToClipboard(encodeURI(document.getElementById("slug-link").textContent));
    });

    document.getElementById("restore-slug-btn")?.addEventListener("click", (_) => {
        // hide slug field and restore slug value
        slugField.value = currentSlug;
        toggleSlugMode();
    });
});
