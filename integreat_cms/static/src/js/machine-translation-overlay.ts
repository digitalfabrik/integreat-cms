import { getCsrfToken } from "./utils/csrf-token";

const resetValue = 0;
const budgetThreshold = 0;
const limitOfPreview = 5;

type PageAttributes = {
    [id: number]: { id: number; title: string; words: number; hix: boolean };
};
type Pages = {
    [category: string]: PageAttributes;
};

const toggleMachineTranslationForPagesButton = () => {
    // Only activate button if budget is sufficient
    const budget: number = +document.getElementById("machine-translation-overlay-budget-remains-result").innerText;
    const MachineTranslationButton = document.getElementById(
        "machine-translation-overlay-bulk-action-execute"
    ) as HTMLButtonElement;
    if (budget >= budgetThreshold && document.getElementById("machine-translation-overlay-pages").hasChildNodes()) {
        MachineTranslationButton.disabled = false;
    } else {
        MachineTranslationButton.disabled = true;
    }
};

const getSelectedIDs = () => {
    // get the IDs of the selected pages
    const selectedItems = document.querySelectorAll(".bulk-select-item:checked");
    const selectedPages: Array<number> = [];
    selectedItems.forEach((selectedItem) => {
        selectedPages.push(parseInt((selectedItem as HTMLInputElement).value, 10));
    });
    return selectedPages;
};

const getAllPages = async (url: string, selectedPages: Array<number>): Promise<Pages> => {
    // make AJAX call to get all pages and return them as Promise <object>
    const response = await fetch(url, {
        method: "POST",
        headers: {
            "X-CSRFToken": getCsrfToken(),
        },
        body: JSON.stringify(selectedPages),
    });
    const pages = await response.json();
    return pages;
};

const calculateAndSetRemainingBudget = () => {
    // calculate and set the remaining budget after translation will be executed and call toggleMachineTranslationForPagesButton in case the budget is not sufficient
    const currentBudgetElement: number = +document.getElementById("machine-translation-overlay-current-budget-result")
        .innerText;
    const usageOfBudgetElement: number = +document.getElementById("machine-translation-overlay-budget-usage-result")
        .innerText;
    const remainingBudgetElement = document.getElementById("machine-translation-overlay-budget-remains-result");
    const remainingBudget = currentBudgetElement - usageOfBudgetElement;
    remainingBudgetElement.textContent = remainingBudget.toString();
    toggleMachineTranslationForPagesButton();
};

const buildTranslatableList = (
    translatablePages: PageAttributes,
    previewListOfPages: HTMLElement,
    listOfOptionalPages: HTMLElement
) => {
    const pages = Object.values(translatablePages);

    let numberOfTranslatablePages = resetValue;
    let numberOfWords = resetValue;

    pages.forEach((page) => {
        const list = document.createElement("li");
        list.classList.add("list-disc", "ml-4");
        list.textContent = page.title;

        if (previewListOfPages.children.length < limitOfPreview) {
            previewListOfPages.appendChild(list);
        } else {
            listOfOptionalPages.appendChild(list);
        }

        numberOfTranslatablePages += 1;
        numberOfWords += page.words;
    });

    document.getElementById("machine-translation-overlay-pages-number").textContent =
        numberOfTranslatablePages.toString();
    document.getElementById("machine-translation-overlay-budget-usage-result").textContent = numberOfWords.toString();
    calculateAndSetRemainingBudget();
};

const buildNotTranslatableList = (notTranslatablePages: PageAttributes, expandableWarningListElement: HTMLElement) => {
    const pages = Object.values(notTranslatablePages);

    let numberOfNotTranslatablePages = 0;

    pages.forEach((page) => {
        const list = document.createElement("li");
        list.classList.add("list-disc", "ml-4");
        list.textContent = page.title;
        expandableWarningListElement.appendChild(list);
        numberOfNotTranslatablePages += 1;
    });

    document.getElementById("not-translatable").textContent = numberOfNotTranslatablePages.toString();
};

const prepareOverlay = (filteredPages: Pages) => {
    const previewListOfPages = document.getElementById("machine-translation-overlay-pages");
    previewListOfPages.textContent = "";
    const listOfOptionalPages = document.getElementById("machine-translation-overlay-pages-optional");
    listOfOptionalPages.textContent = "";
    buildTranslatableList(filteredPages.translatable, previewListOfPages, listOfOptionalPages);

    const warningListElement = document.getElementById("machine-translation-overlay-warning");
    const expandableWarningListElement = document.getElementById("machine-translation-overlay-warning-optional");
    expandableWarningListElement.textContent = "";
    buildNotTranslatableList(filteredPages.not_translatable, expandableWarningListElement);

    const expansionTrigger = document.getElementById("machine-translation-overlay-expansion-trigger");
    const noPageWarning = document.getElementById("machine-translation-overlay-pages-no-pages-warning");

    if (previewListOfPages.children.length === 0) {
        noPageWarning.classList.remove("hidden");
    } else {
        noPageWarning.classList.add("hidden");
    }

    if (listOfOptionalPages.children.length === 0) {
        expansionTrigger.classList.add("hidden");
        expansionTrigger.classList.remove("block");
    } else {
        expansionTrigger.classList.remove("hidden");
        expansionTrigger.classList.add("block");
    }

    toggleMachineTranslationForPagesButton();

    if (expandableWarningListElement.children.length !== 0) {
        warningListElement.classList.add("block");
        warningListElement.classList.remove("hidden");
    } else {
        warningListElement.classList.remove("block");
        warningListElement.classList.add("hidden");
    }
};

const setAmountOfSelectedPages = (numberOfSelectedPages: number) => {
    // set the number of selected pages
    const numberOfSelectedPagesElement = document.getElementById("machine-translation-overlay-pages-total-number");
    numberOfSelectedPagesElement.textContent = numberOfSelectedPages.toString();
};

const closeMachineTranslationOverlay = (overlay: HTMLElement) => {
    // close overlay
    overlay.classList.add("hidden");
    overlay.classList.remove("flex");
};

const toggleOptionalText = (trigger: HTMLElement, optionalText: HTMLElement) => {
    // function to toggle optional text
    trigger.addEventListener("click", () => {
        optionalText.classList.toggle("hidden");
        optionalText.classList.toggle("block");
        if (optionalText.classList.contains("block")) {
            trigger.textContent = trigger.dataset.alternativeText; // eslint-disable-line no-param-reassign
        } else {
            trigger.textContent = trigger.dataset.defaultText; // eslint-disable-line no-param-reassign
        }
    });
};

const addMachineTranslationOverlayEventListeners = () => {
    // add event listeners to overlay
    const overlay = document.getElementById("machine-translation-overlay");
    const provider = document.getElementById("machine-translation-option").getAttribute("data-mt-provider");
    if (overlay && provider === "DeepL") {
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

                filteredPages.then((filteredPages: Pages) => {
                    prepareOverlay(filteredPages);
                });
                setAmountOfSelectedPages(selectedIDs.length);
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

        toggleOptionalText(
            document.getElementById("machine-translation-overlay-warning-more"),
            document.getElementById("machine-translation-overlay-warning-optional")
        );
        toggleOptionalText(
            document.getElementById("machine-translation-overlay-expansion-trigger"),
            document.getElementById("machine-translation-overlay-pages-optional")
        );
    }
};

window.addEventListener("load", () => {
    // main function
    addMachineTranslationOverlayEventListeners();
});
