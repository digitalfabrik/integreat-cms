/**
 * This file contains all functions which are needed for the diff calculation of revisions.
 */

import HtmlDiff from "htmldiff-js";

const showPreviewDiff = ({ target }: Event) => {
    const parent = (target as HTMLElement).closest("ul").parentNode;
    parent.querySelector(".xliff-diff-source-code").classList.add("hidden");
    parent.querySelector(".xliff-diff-preview").classList.remove("hidden");
    const showSourceCodeDiff = parent.querySelector(".xliff-show-source-code-diff");
    showSourceCodeDiff.classList.remove("z-10");
    showSourceCodeDiff.classList.add("cursor-pointer");
    showSourceCodeDiff.firstElementChild.classList.add("hover:bg-blue-500", "hover:text-white");
    const showPreviewDiff = parent.querySelector(".xliff-show-preview-diff");
    showPreviewDiff.firstElementChild.classList.remove("hover:bg-blue-500", "hover:text-white");
    showPreviewDiff.classList.remove("cursor-pointer");
    showPreviewDiff.classList.add("z-10");
};

const showSourceCodeDiff = ({ target }: Event) => {
    const parent = (target as HTMLElement).closest("ul").parentNode;
    parent.querySelector(".xliff-diff-preview").classList.add("hidden");
    parent.querySelector(".xliff-diff-source-code").classList.remove("hidden");
    const showPreviewDiff = parent.querySelector(".xliff-show-preview-diff");
    showPreviewDiff.classList.remove("z-10");
    showPreviewDiff.classList.add("cursor-pointer");
    showPreviewDiff.firstElementChild.classList.add("hover:bg-blue-500", "hover:text-white");
    const showSourceCodeDiff = parent.querySelector(".xliff-show-source-code-diff");
    showSourceCodeDiff.firstElementChild.classList.remove("hover:bg-blue-500", "hover:text-white");
    showSourceCodeDiff.classList.remove("cursor-pointer");
    showSourceCodeDiff.classList.add("z-10");
};

window.addEventListener("load", () => {
    // Iterate over revisions and calculate diff
    document.querySelectorAll(".xliff-diff-preview").forEach((xliffImport) => {
        // Calculate the actual diff and insert into the diff div
        /* eslint-disable-next-line no-param-reassign */
        xliffImport.querySelector(".xliff-diff-preview-rendered").innerHTML = HtmlDiff.execute(
            xliffImport.querySelector(".xliff-import-source").innerHTML,
            xliffImport.querySelector(".xliff-import-target").innerHTML
        );
    });

    Array.from(document.getElementsByClassName("xliff-show-preview-diff")).forEach((node) => {
        (node as HTMLElement).addEventListener("click", showPreviewDiff);
    });
    Array.from(document.getElementsByClassName("xliff-show-source-code-diff")).forEach((node) => {
        (node as HTMLElement).addEventListener("click", showSourceCodeDiff);
    });
});
