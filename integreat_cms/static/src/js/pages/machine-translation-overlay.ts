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

const getAllPages = async (
    url: string
): Promise<{ [index: string]: { id: number; title: string; words: number; hix: boolean } }> => {
    // make AJAX call to get all pages and return them as Promise <object>
    let pages;
    await fetch(url, {
        method: "POST",
        headers: {
            "X-CSRFToken": getCsrfToken(),
        },
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

const filterAllPagesByHixValue = (
    pages: { [index: string]: { id: number; title: string; words: number; hix: boolean } },
    selectedPages: Array<Element>
) => {
    // Sets lists of pages that fullfill HIX threshold either to the preview or to the expandable list
    const listOfFirstFivePages = document.getElementById("machine-translation-overlay-pages");
    const listOfOptionalPages = document.getElementById("machine-translation-overlay-pages-optional");
    const expansionTrigger = document.getElementById("machine-translation-overlay-expansion-trigger");

    listOfFirstFivePages.innerHTML = "";
    listOfOptionalPages.innerHTML = "";

    const warningListElement = document.getElementById("machine-translation-overlay-warning");
    const expandableWarningListElement = document.getElementById("machine-translation-overlay-warning-optional");
    expandableWarningListElement.innerHTML = "";

    let numberOfTranslatablePages = 0;
    let numberOfNotTranslatablePages = 0;
    let numbrtOfWords = 0;

    selectedPages.forEach((page) => {
        const index = page.getAttribute("data-drop-id");
        type ObjectKey = keyof typeof pages;
        const key = index as ObjectKey;

        const list = document.createElement("li");
        list.classList.add("list-disc");
        list.classList.add("ml-4");

        if (pages[key].hix) {
            list.textContent = pages[key].title;
            numberOfTranslatablePages += 1;
            numbrtOfWords += pages[key].words;
            if (listOfFirstFivePages.children.length <= limitOfPreview) {
                listOfFirstFivePages.appendChild(list);
            } else {
                listOfOptionalPages.appendChild(list);
            }
        } else {
            list.textContent = pages[key].title;
            expandableWarningListElement.appendChild(list);
            numberOfNotTranslatablePages += 1;
        }
    });

    setRequiredBudget(numbrtOfWords);
    document.getElementById("machine-translation-overlay-warning-number").textContent =
        numberOfNotTranslatablePages.toString();

    if (listOfFirstFivePages.children.length > limitOfPreview) {
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

    return numberOfTranslatablePages;
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
                const pages = getAllPages(
                    (document.getElementById("machine-translation-option") as HTMLElement).dataset.url
                );
                const selectedPages = getSelectedItems();

                event.preventDefault();
                overlay.classList.remove("hidden");
                overlay.classList.add("flex");

                pages.then((pages: { [index: string]: { id: number; title: string; words: number; hix: boolean } }) => {
                    const numberOfTranslatablePages = filterAllPagesByHixValue(pages, selectedPages);
                    setAmount(numberOfTranslatablePages);
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
