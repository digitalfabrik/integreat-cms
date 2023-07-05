import { getCsrfToken } from "./utils/csrf-token";

const resetValue = 0;
const budgetThreshold = 0;
const limitOfPreview = 5;

type ContentAttributes = {
    [id: number]: { id: number; title: string; words: number; hix: boolean };
};
type Content = {
    [category: string]: ContentAttributes;
};

const toggleMachineTranslationButton = () => {
    // Only activate button if budget is sufficient
    const budget: number = +document.getElementById("machine-translation-overlay-budget-remains-result").innerText;
    const MachineTranslationButton = document.getElementById(
        "machine-translation-overlay-bulk-action-execute"
    ) as HTMLButtonElement;
    if (budget >= budgetThreshold && document.getElementById("preview-list").hasChildNodes()) {
        MachineTranslationButton.disabled = false;
    } else {
        MachineTranslationButton.disabled = true;
    }
};

const getSelectedIDs = () => {
    // get the IDs of the selected content items
    const selectedItems = document.querySelectorAll(".bulk-select-item:checked");
    const selectedContent: Array<number> = [];
    selectedItems.forEach((selectedItem) => {
        selectedContent.push(parseInt((selectedItem as HTMLInputElement).value, 10));
    });
    return selectedContent;
};

const getContent = async (url: string, selectedContent: Array<number>): Promise<Content> => {
    // make AJAX call to get all data and return them as Promise <object>
    const response = await fetch(url, {
        method: "POST",
        headers: {
            "X-CSRFToken": getCsrfToken(),
        },
        body: JSON.stringify(selectedContent),
    });
    const content = await response.json();
    return content;
};

const calculateAndSetRemainingBudget = () => {
    // calculate and set the remaining budget after translation will be executed and call toggleMachineTranslationButton in case the budget is not sufficient
    const currentBudgetElement: number = +document.getElementById("machine-translation-overlay-current-budget-result")
        .innerText;
    const usageOfBudgetElement: number = +document.getElementById("machine-translation-overlay-budget-usage-result")
        .innerText;
    const remainingBudgetElement = document.getElementById("machine-translation-overlay-budget-remains-result");
    const remainingBudget = currentBudgetElement - usageOfBudgetElement;
    remainingBudgetElement.textContent = remainingBudget.toString();
    toggleMachineTranslationButton();
};

const buildTranslatableList = (
    translatableContent: ContentAttributes,
    previewList: HTMLElement,
    listOfOptionalContent: HTMLElement
) => {
    const contents = Object.values(translatableContent);

    let numberOfTranslatableContent = resetValue;
    let numberOfWords = resetValue;

    contents.forEach((content) => {
        const list = document.createElement("li");
        list.classList.add("list-disc", "ml-4");
        list.textContent = content.title;

        if (previewList.children.length < limitOfPreview) {
            previewList.appendChild(list);
        } else {
            listOfOptionalContent.appendChild(list);
        }

        numberOfTranslatableContent += 1;
        numberOfWords += content.words;
    });

    document.getElementById("number-of-translatable-content").textContent = numberOfTranslatableContent.toString();
    document.getElementById("machine-translation-overlay-budget-usage-result").textContent = numberOfWords.toString();
    calculateAndSetRemainingBudget();
};

const buildNotTranslatableList = (
    notTranslatableContent: ContentAttributes,
    expandableWarningListElement: HTMLElement
) => {
    const contents = Object.values(notTranslatableContent);

    let numberOfNotTranslatableContent = 0;

    contents.forEach((content) => {
        const list = document.createElement("li");
        list.classList.add("list-disc", "ml-4");
        list.textContent = content.title;
        expandableWarningListElement.appendChild(list);
        numberOfNotTranslatableContent += 1;
    });

    document.getElementById("not-translatable").textContent = numberOfNotTranslatableContent.toString();
};

const prepareOverlay = (filteredContent: Content) => {
    const previewList = document.getElementById("preview-list");
    previewList.textContent = "";
    const listOfOptionalContent = document.getElementById("list-of-optional-content");
    listOfOptionalContent.textContent = "";
    buildTranslatableList(filteredContent.translatable, previewList, listOfOptionalContent);

    const warningListElement = document.getElementById("machine-translation-overlay-warning");
    const expandableWarningListElement = document.getElementById("machine-translation-overlay-warning-optional");
    expandableWarningListElement.textContent = "";
    buildNotTranslatableList(filteredContent.not_translatable, expandableWarningListElement);

    const expansionTrigger = document.getElementById("machine-translation-overlay-expansion-trigger");
    const noPageWarning = document.getElementById("no-content-warning");

    if (previewList.children.length === 0) {
        noPageWarning.classList.remove("hidden");
    } else {
        noPageWarning.classList.add("hidden");
    }

    if (listOfOptionalContent.children.length === 0) {
        expansionTrigger.classList.add("hidden");
        expansionTrigger.classList.remove("block");
    } else {
        expansionTrigger.classList.remove("hidden");
        expansionTrigger.classList.add("block");
    }

    toggleMachineTranslationButton();

    if (expandableWarningListElement.children.length !== 0) {
        warningListElement.classList.add("block");
        warningListElement.classList.remove("hidden");
    } else {
        warningListElement.classList.remove("block");
        warningListElement.classList.add("hidden");
    }
};

const setAmountOfSelectedContent = (numberOfSelectedContent: number) => {
    // set the number of selected content items
    const numberOfSelectedContentElement = document.getElementById("number-of-selected-content");
    numberOfSelectedContentElement.textContent = numberOfSelectedContent.toString();
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
                const filteredContent = getContent(url, selectedIDs);

                event.preventDefault();
                overlay.classList.remove("hidden");
                overlay.classList.add("flex");

                filteredContent.then((filteredContent: Content) => {
                    prepareOverlay(filteredContent);
                });
                setAmountOfSelectedContent(selectedIDs.length);
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
            document.getElementById("list-of-optional-content")
        );
    }
};

window.addEventListener("load", () => {
    // main function
    addMachineTranslationOverlayEventListeners();
});
