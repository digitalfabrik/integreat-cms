import { getCsrfToken } from "../utils/csrf-token";

type Content = {
    broken_links: number;
    relevant_translation: string;
    edit_url: string;
};

const getContent = async (url: string): Promise<Content> => {
    const response = await fetch(url, {
        method: "POST",
        headers: {
            "X-CSRFToken": getCsrfToken(),
        },
    });
    return response.json();
};

window.addEventListener("load", async () => {
    const brokenLinksElement = document.getElementById("broken-links");

    if (!brokenLinksElement) {
        return;
    }

    const url = brokenLinksElement.dataset.url;
    const hideWaitingMessage = () => {
        brokenLinksElement.querySelector(".waiting-message").classList.add("hidden");
    };

    const showSuccessMessage = () => {
        brokenLinksElement.querySelector(".success-message").classList.remove("hidden");
    };

    const showSuccessIcon = () => {
        brokenLinksElement.querySelector(".success-icon").classList.remove("hidden");
    };

    const showDescription = (affectedPageTitle: string) => {
        brokenLinksElement.querySelector(".todo-message").classList.remove("hidden");
        (brokenLinksElement.querySelector(".todo-message b") as HTMLElement).innerText = affectedPageTitle;
    };

    const showNumberOfPagesElement = () => {
        brokenLinksElement.querySelector(".total-results").classList.remove("hidden");
    };

    const updateNumberOfPages = (numberOfPages: number) => {
        (brokenLinksElement.querySelector(".total-results span") as HTMLElement).innerText = numberOfPages.toString();
    };

    const setLink = (editURL: string) => {
        (brokenLinksElement.querySelector(".todo-button a") as HTMLAnchorElement).href = editURL;
    };

    const showButton = (editURL: string) => {
        brokenLinksElement.querySelector(".todo-button").classList.remove("hidden");
        setLink(editURL);
    };

    if (url) {
        const json = await getContent(url);
        hideWaitingMessage();
        showNumberOfPagesElement();
        if (json.broken_links > 0) {
            showDescription(json.relevant_translation);
            updateNumberOfPages(json.broken_links);
            showButton(json.edit_url);
        } else {
            showSuccessMessage();
            showSuccessIcon();
            updateNumberOfPages(0);
        }
    }
});
