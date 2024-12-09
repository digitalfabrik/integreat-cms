/* const showAllTotalNumbers = () => {
    const elements = document.querySelectorAll<HTMLElement>(".total-results");

    elements.forEach((element) => {
        if (!element.closest("#broken-links") && !element.closest("#translation-coverage")) {
            const el = element;
            el.classList.remove("hidden");
        }
    });
};

showAllTotalNumbers();

export const hideWaitingMessage = (element: HTMLElement) => {
    element.querySelector(".waiting-message").classList.add("hidden");
};

export const showSuccessMessage = (element: HTMLElement) => {
    element.querySelector(".success-message").classList.remove("hidden");
};

export const showSuccessIcon = (element: HTMLElement) => {
    element.querySelector(".success-icon").classList.remove("hidden");
};

export const showDescription = (element: HTMLElement, affectedPageTitle: string) => {
    element.querySelector(".todo-message").classList.remove("hidden");
    (element.querySelector(".todo-message b") as HTMLElement).innerText = affectedPageTitle;
};

export const showNumberOfPagesElement = (element: HTMLElement, ) => {
    element.querySelector(".total-results").classList.remove("hidden");
};

export const updateNumberOfPages = (element: HTMLElement, numberOfPages: number) => {
    (element.querySelector(".total-results span") as HTMLElement).innerText = numberOfPages.toString();
};
*/
