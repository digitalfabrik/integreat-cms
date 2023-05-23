/* eslint no-magic-numbers: ["error", { "ignore": [0, 1, 3] }] */
import { getCsrfToken } from "../utils/csrf-token";

const limitOfPreview = 5;

const toggleMachineTranslationForPagesButton = () => {
    // Only activate button if budget is enough
    const budget = document.getElementById("machine-translation-overlay-budget-remains-result")
        .innerText as any as number;
    const MachineTranslationButton = document.getElementById(
        "machine-translation-overlay-bulk-action-execute"
    ) as HTMLButtonElement;
    if (budget >= 0 && document.getElementById("machine-translation-overlay-pages").children.length > 0) {
        MachineTranslationButton.disabled = false;
    } else {
        MachineTranslationButton.disabled = true;
    }
};

const getSelectedItems = () => {
    // get the HTML tr element of the selected pages
    const checkboxes = document.querySelectorAll(".bulk-select-item");
    const selectedPages: Array<Element> = [];
    checkboxes.forEach((checkbox) => {
        if ((checkbox as HTMLInputElement).checked) {
            selectedPages.push(checkbox.closest("tr"));
        }
    });
    return selectedPages;
};

const getSelectedIDs = () => {
    // get the HTML tr element of the selected pages
    const checkboxes = document.querySelectorAll(".bulk-select-item");
    const selectedPages: Array<number> = [];
    checkboxes.forEach((checkbox) => {
        if ((checkbox as HTMLInputElement).checked) {
            selectedPages.push(parseInt(checkbox.closest("tr").getAttribute("data-drop-id")));
        }
    });
    return selectedPages;
};

const getAllPages = async (
    url: string, selectedPages: Array<number>
): Promise<{[category: string]: {[id: number]: { id: number; title: string; words: number; hix: boolean }}}> => {
    // make AJAX call to get all pages and return them as Promise <object>
    let pages;
    await fetch(url, {
        method: "POST",
        headers: {
            "X-CSRFToken": getCsrfToken(),
        },
        body: JSON.stringify(selectedPages),
    })
        .then((response) => response.json())
        .then((json) => {
            pages = json;
        })
        .then();
    return pages;
};

const calculateAndSetRemainingBudget = () => {
    // calculate and set the remaining budget after translation will be executed and call toggleMachineTranslationForPagesButton in case the budget is not sufficient
    const currentBudgetElement = document.getElementById("machine-translation-overlay-current-budget-result")
        .innerText as any as number;
    const usageOfBudgetElement = document.getElementById("machine-translation-overlay-budget-usage-result")
        .innerText as any as number;
    const remainingBudgetElement = document.getElementById("machine-translation-overlay-budget-remains-result");
    const remainingBudget = currentBudgetElement - usageOfBudgetElement;
    remainingBudgetElement.textContent = remainingBudget as unknown as string;
    toggleMachineTranslationForPagesButton();
};

const setRequiredBudget = (sum: number) => {
    // set the number of words that would be needed for the attempted machine translation, and afterwards call calculateAndSetRemainingBudget for next steps
    const resultElement = document.getElementById("machine-translation-overlay-budget-usage-result");
    resultElement.textContent = "";
    resultElement.textContent = sum as any as string;
    calculateAndSetRemainingBudget();
};

const getPageTitles = (selectedPages: Array<Element>) => {
    // get titles of selected pages and store them in an array
    const titles: Array<string> = [];
    selectedPages.forEach((row) => {
        titles.push((row.children[3].children[0] as HTMLElement).title.trim());
    });
    return titles;
};

const buildTranslatableList = (
    translatablePages: {[id: number]: { id: number; title: string; words: number; hix: boolean; };},
    listOfFirstFivePages: HTMLElement,
    listOfOptionalPages: HTMLElement) => {
    
    const pages = Object.values(translatablePages);

    let numberOfTranslatablePages = 0;
    let numberOfWords = 0;

    pages.forEach((page) => {
        const list = document.createElement("li");
        list.classList.add("list-disc");
        list.classList.add("ml-4");
        list.textContent = page["title"];
        
        if (listOfFirstFivePages.children.length < limitOfPreview) {
            listOfFirstFivePages.appendChild(list);
        } else {
            listOfOptionalPages.appendChild(list);
        }

        numberOfTranslatablePages += 1;
        numberOfWords += page["words"];
    });

    setAmount(numberOfTranslatablePages);
    setRequiredBudget(numberOfWords);
}

const buildNotTranslatableList = (
    translatablePages: {[id: number]: { id: number; title: string; words: number; hix: boolean; };},
    expandableWarningListElement: HTMLElement) => {
    
    const pages = Object.values(translatablePages);

    let numberOfNotTranslatablePages = 0;

    pages.forEach((page) => {
        const list = document.createElement("li");
        list.classList.add("list-disc");
        list.classList.add("ml-4");
        list.textContent = page["title"];
        expandableWarningListElement.appendChild(list);

        numberOfNotTranslatablePages += 1;
    });

    document.getElementById("machine-translation-overlay-warning-number").textContent =
        numberOfNotTranslatablePages.toString();
}

const prepareOverlay = (filteredPages: 
            {[category: string]: {[id: number]: { id: number; title: string; words: number; hix: boolean }}}) => {
    
    const translatablePages = filteredPages["translatable"];
    const listOfFirstFivePages = document.getElementById("machine-translation-overlay-pages");
    listOfFirstFivePages.innerHTML = "";
    const listOfOptionalPages = document.getElementById("machine-translation-overlay-pages-optional");
    listOfOptionalPages.innerHTML = "";
    buildTranslatableList(translatablePages, listOfFirstFivePages, listOfOptionalPages);

    const notTranslatablePages = filteredPages["not_translatable"];
    const warningListElement = document.getElementById("machine-translation-overlay-warning");
    const expandableWarningListElement = document.getElementById("machine-translation-overlay-warning-optional");
    expandableWarningListElement.innerHTML = "";
    buildNotTranslatableList(notTranslatablePages, expandableWarningListElement);
    
    const expansionTrigger = document.getElementById("machine-translation-overlay-expansion-trigger");
    if (listOfFirstFivePages.children.length >= limitOfPreview) {
        expansionTrigger.classList.add("block");
        expansionTrigger.classList.remove("hidden");
    } else {
        expansionTrigger.classList.add("hidden");
        expansionTrigger.classList.remove("block");
    }
    toggleMachineTranslationForPagesButton();

    if (expandableWarningListElement.children.length !== 0) {
        warningListElement.classList.add("block");
        warningListElement.classList.remove("hidden");
    }
};

const setAmount = (amountOfValidPages: number) => {
    // Display the number of valid pages to the according HTML element
    const amountElement = document.getElementById("machine_translation_overlay_pages_number");
    amountElement.textContent = amountOfValidPages as unknown as string;
};

const calculateNumberOfSelectedPages = () => getPageTitles(getSelectedItems()).length;

const setAmountOfSelectedPages = (numberOfSelectedPages: number) => {
    // set the number of selected pages
    const numberOfSelectedPagesElement = document.getElementById("machine_translation_overlay_pages_total_number");
    numberOfSelectedPagesElement.textContent = numberOfSelectedPages as any as string;
};

const closeMachineTranslationOverlay = (overlay: HTMLElement) => {
    // close overlay
    overlay.classList.add("hidden");
    overlay.classList.remove("flex");
};

const toggleOptionalText = (trigger: HTMLElement, target: HTMLElement) => {
    // function to toggle optional text
    trigger.addEventListener("click", () => {
        target.classList.toggle("hidden");
        target.classList.toggle("block");
        if (target.classList.contains("block")) {
            trigger.textContent = trigger.dataset.alternativeText; // eslint-disable-line no-param-reassign
        } else {
            trigger.textContent = trigger.dataset.defaultText; // eslint-disable-line no-param-reassign
        }
    });
};

const addMachineTranslationOverlayEventListeners = () => {
    // add event listeners to overlay
    const overlay = document.getElementById("machine_translation_overlay");

    if (overlay) {
        // Set listener for bulk action execute button.
        document.getElementById("bulk-action-execute")?.addEventListener("click", (event) => {
            const machineTranslationOptionIndex = (
                document.getElementById("machine-translation-option") as HTMLOptionElement
            ).index;
            const { selectedIndex } = document.getElementById("bulk-action") as HTMLSelectElement;

            if (machineTranslationOptionIndex === selectedIndex) {
                const url = (document.getElementById("machine-translation-option") as HTMLElement).dataset.url;
                const selectedIDs = getSelectedIDs();
                const filteredPages = getAllPages(url, selectedIDs);

                event.preventDefault();
                overlay.classList.remove("hidden");
                overlay.classList.add("flex");

                filteredPages.then((filteredPages: {[category: string]: {[id: number]: { id: number; title: string; words: number; hix: boolean }}}) => {
                    prepareOverlay(filteredPages);
                });

                toggleOptionalText(
                    document.getElementById("machine-translation-overlay-expansion-trigger"),
                    document.getElementById("machine-translation-overlay-pages-optional")
                );
                toggleOptionalText(
                    document.getElementById("machine-translation-overlay-warning-more"),
                    document.getElementById("machine-translation-overlay-warning-optional")
                );
                setAmountOfSelectedPages(calculateNumberOfSelectedPages());
            }
        });
        document.getElementById("btn-close-machine-translation-overlay").addEventListener("click", () => {
            closeMachineTranslationOverlay(overlay);
        });
        // Close window by clicking on backdrop.
        overlay.addEventListener("click", (e) => {
            if (e.target === overlay) {
                closeMachineTranslationOverlay(overlay);
            }
        });
    }
};

window.addEventListener("load", () => {
    // main function
    addMachineTranslationOverlayEventListeners();
});
