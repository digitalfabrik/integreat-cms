/* eslint no-magic-numbers: ["error", { "ignore": [0, 1, 3, 4, 5, 15] }] */
import { getCsrfToken } from "../utils/csrf-token";

const toggleMachineTranslationForPagesButton = () => {
    // Only activate button if budget is enough
    const budget = document.getElementById("machine-translation-overlay-budget-remains-result")
        .innerText as any as number;
    const MachineTranslationButton = document.getElementById(
        "machine-translation-overlay-bulk-action-execute"
    ) as HTMLButtonElement;
    if (budget > 0 && document.getElementById("machine-translation-overlay-pages").children.length > 0) {
        MachineTranslationButton.disabled = false;
    } else {
        MachineTranslationButton.disabled = true;
    }
};

const getSelectedItems = () => {
    const checkboxes = document.querySelectorAll(".bulk-select-item");
    const selectedPages: Array<Element> = [];
    checkboxes.forEach((checkbox) => {
        if ((checkbox as HTMLInputElement).checked) {
            selectedPages.push(checkbox.closest("tr"));
        }
    });
    return selectedPages;
};

const getPagesAndHixValueForPages = async (url: string) => {
    let result;
    await fetch(url, {
        method: "POST",
        headers: {
            "X-CSRFToken": getCsrfToken(),
        },
    })
        .then((response) => response.json())
        .then((json) => {
            result = json;
        })
        .then();
    return result;
};

const setRemainingBudget = () => {
    const currentBudget = document.getElementById("machine-translation-overlay-current-budget-result")
        .innerText as any as number;
    const usageOfBudget = document.getElementById("machine-translation-overlay-budget-usage-result")
        .innerText as any as number;
    const remainingBudget = currentBudget - usageOfBudget;
    document.getElementById("machine-translation-overlay-budget-remains-result").innerHTML =
        remainingBudget as unknown as string;
    toggleMachineTranslationForPagesButton();
};

const setRequiredBudget = (sum: number) => {
    document.getElementById("machine-translation-overlay-budget-usage-result").innerHTML = "";
    document.getElementById("machine-translation-overlay-budget-usage-result").innerHTML = sum as any as string;
    setRemainingBudget();
};

const calculateNeededBudget = (pages: Promise<object>, pageTitles: Array<string>) => {
    pages.then((loadedPages) => {
        let sum = 0;
        const values = Object.values(loadedPages);
        values.forEach((value) => {
            if (pageTitles.includes(value.title)) {
                if (value.hix_score >= 15) {
                    sum += value.amount_of_words;
                }
            }
        });
        setRequiredBudget(sum);
    });
};

const getAllPages = (selectedPages: Array<Element>) => {
    const titles: Array<string> = [];
    selectedPages.forEach((row) => {
        titles.push((row.children[3].children[0] as HTMLElement).title.trim());
    });
    return titles;
};

const setPagesWarning = (pageTitles: Array<string>) => {
    let sum = 0;
    document.getElementById("machine-translation-overlay-warning").classList.add("block");
    document.getElementById("machine-translation-overlay-warning").classList.remove("hidden");
    const selectedPages = getAllPages(getSelectedItems());
    document.getElementById("machine-translation-overlay-warning-optional").innerHTML = "";
    pageTitles.forEach((title) => {
        if (selectedPages.includes(title)) {
            const list = document.createElement("li");
            list.textContent = title as string;
            list.classList.add("list-disc");
            list.classList.add("ml-4");
            sum += 1;
            document.getElementById("machine-translation-overlay-warning-optional").appendChild(list);
        }
    });
    document.getElementById("machine-translation-overlay-warning-number").innerHTML = sum as any as string;
    if (document.getElementById("machine-translation-overlay-warning-optional").children.length === 0) {
        document.getElementById("machine-translation-overlay-warning").classList.remove("block");
        document.getElementById("machine-translation-overlay-warning").classList.add("hidden");
    }
};

const setPages = (pageTitles: Array<string>) => {
    document.getElementById("machine-translation-overlay-pages").innerHTML = "";
    document.getElementById("machine-translation-overlay-pages-optional").innerHTML = "";
    const selectedPages = getAllPages(getSelectedItems());
    pageTitles.forEach((title, i) => {
        if (selectedPages.includes(title)) {
            const list = document.createElement("li");
            list.textContent = title as string;
            list.classList.add("list-disc");
            list.classList.add("ml-4");
            if (i <= 4) {
                document.getElementById("machine-translation-overlay-pages").appendChild(list);
            } else {
                document.getElementById("machine-translation-overlay-pages-optional").appendChild(list);
            }
        }
    });
    if (pageTitles.length > 5) {
        document.getElementById("machine-translation-overlay-more").classList.add("block");
        document.getElementById("machine-translation-overlay-more").classList.remove("hidden");
    } else {
        document.getElementById("machine-translation-overlay-more").classList.add("hidden");
        document.getElementById("machine-translation-overlay-more").classList.remove("block");
    }
    toggleMachineTranslationForPagesButton();
    if (document.getElementById("machine-translation-overlay-pages").children.length === 0) {
        if (
            document.getElementById("machine-translation-overlay-pages-no-pages-warning").classList.contains("hidden")
        ) {
            document.getElementById("machine-translation-overlay-pages-no-pages-warning").classList.remove("hidden");
            document.getElementById("machine-translation-overlay-pages-no-pages-warning").classList.add("block");
        }
    } else {
        document.getElementById("machine-translation-overlay-pages-no-pages-warning").classList.add("hidden");
        document.getElementById("machine-translation-overlay-pages-no-pages-warning").classList.remove("block");
    }
};

const setAmount = (allPages: Array<string>) => {
    let sum = 0;
    const selectedPages = getAllPages(getSelectedItems());
    allPages.forEach((page) => {
        if (selectedPages.includes(page)) {
            sum += 1;
        }
    });
    document.getElementById("machine_translation_overlay_languages_number").innerText = sum as unknown as string;
};

const filterPagesByHixValue = (pages: Promise<object>) => {
    pages.then((loadedPages) => {
        const titlesForFullfilledHix: Array<string> = [];
        const titlesForNotFullfilledHix: Array<string> = [];
        const values = Object.values(loadedPages);
        values.forEach((value) => {
            if (value.hix_score >= 15) {
                titlesForFullfilledHix.push(value.title);
            } else {
                titlesForNotFullfilledHix.push(value.title);
            }
        });
        setPages(titlesForFullfilledHix);
        setAmount(titlesForFullfilledHix);
        setPagesWarning(titlesForNotFullfilledHix);
    });
};

const closeMachineTranslationOverlay = (overlay: HTMLElement) => {
    overlay.classList.add("hidden");
    overlay.classList.remove("flex");
};

const toggleOptionalText = (trigger: HTMLElement, target: HTMLElement) => {
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
    const overlay = document.getElementById("machine_translation_overlay");
    if (overlay) {
        // Set listener for bulk action execute button.
        document.getElementById("bulk-action-execute")?.addEventListener("click", (event) => {
            const machineTranslationOptionIndex = (
                document.getElementById("machine-translation-option") as HTMLOptionElement
            ).index;
            const { selectedIndex } = document.getElementById("bulk-action") as HTMLSelectElement;
            if (machineTranslationOptionIndex === selectedIndex) {
                event.preventDefault();
                overlay.classList.remove("hidden");
                overlay.classList.add("flex");
                calculateNeededBudget(
                    getPagesAndHixValueForPages(
                        (document.getElementById("machine-translation-option") as HTMLElement).dataset.url
                    ),
                    getAllPages(getSelectedItems())
                );
                filterPagesByHixValue(
                    getPagesAndHixValueForPages(
                        (document.getElementById("machine-translation-option") as HTMLElement).dataset.url
                    )
                );
                toggleOptionalText(
                    document.getElementById("machine-translation-overlay-more"),
                    document.getElementById("machine-translation-overlay-pages-optional")
                );
                toggleOptionalText(
                    document.getElementById("machine-translation-overlay-warning-more"),
                    document.getElementById("machine-translation-overlay-warning-optional")
                );
            }
        });
        document.getElementById("btn-close-machine-translation-overlay").addEventListener("click", () => {
            console.log("clicked");
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
    addMachineTranslationOverlayEventListeners();
});
