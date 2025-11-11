/**
 * used in:
 * number_of_missing_or_outdated_translations_row.html > todo_dashboard_widget.html > dashboard.html
 */
import { getCsrfToken } from "../../utils/csrf-token";

type Content = {
    number_of_missing_or_outdated_translations: number;
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

const showAllTotalNumbers = () => {
    const elements = document.querySelectorAll<HTMLElement>(".total-results");

    elements.forEach((element) => {
        if (!element.closest("#translation-coverage")) {
            const el = element;
            el.classList.remove("hidden");
        }
    });
};

window.addEventListener("load", async () => {
    showAllTotalNumbers();

    const translationCoverageElement = document.getElementById("translation-coverage");

    if (!translationCoverageElement) {
        return;
    }

    const url = translationCoverageElement.dataset.url;
    const hideWaitingMessage = () => {
        translationCoverageElement.querySelector(".waiting-message").classList.add("hidden");
    };

    const showSuccessMessage = () => {
        translationCoverageElement.querySelector(".success-message").classList.remove("hidden");
    };

    const showSuccessIcon = () => {
        translationCoverageElement.querySelector(".success-icon").classList.remove("hidden");
    };

    const showDescription = (affectedPageTitle: string) => {
        translationCoverageElement.querySelector(".todo-message").classList.remove("hidden");
        (translationCoverageElement.querySelector(".todo-message b") as HTMLElement).innerText = affectedPageTitle;
    };

    const showNumberOfPagesElement = () => {
        translationCoverageElement.querySelector(".total-results").classList.remove("hidden");
    };

    const updateNumberOfPages = (numberOfPages: number) => {
        (translationCoverageElement.querySelector(".total-results span") as HTMLElement).innerText =
            numberOfPages.toString();
    };

    const showButton = () => {
        translationCoverageElement.querySelector(".todo-button").classList.remove("hidden");
    };

    if (url) {
        const json = await getContent(url);
        hideWaitingMessage();
        showNumberOfPagesElement();
        if (json.number_of_missing_or_outdated_translations > 0) {
            showDescription(String(json.number_of_missing_or_outdated_translations));
            updateNumberOfPages(json.number_of_missing_or_outdated_translations);
            showButton();
        } else {
            showSuccessMessage();
            showSuccessIcon();
            updateNumberOfPages(0);
        }
    }
});
