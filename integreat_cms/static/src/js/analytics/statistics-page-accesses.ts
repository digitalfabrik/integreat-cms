/* Category as returned by get_page_accesses_ajax in statistics_actions.py is either a language slug or "total_accesses" */
type AccessesPerLanguageAndInTotal = {
    [category: string]: number;
};

type AjaxResponse = {
    [id: string]: AccessesPerLanguageAndInTotal;
};

let statisticsForm: HTMLFormElement;
let pageAccessesURL: string;
let pageAccessesForm: HTMLFormElement;
let ajaxRequestID: number;
let exportTable: string[][] = [];
let visibleDatasetSlugs: string[];

/**
 * Remove updateSelectionCount and setCheckboxRecursively (issue 4430)
 * Import them from ../feature/bulk-actions instead
 */
const updateSelectionCount = () => {
    const selectCount = document.querySelector("[data-list-selection-count]") as HTMLElement;
    if (selectCount) {
        selectCount.innerText = document.querySelectorAll(".bulk-select-item:checked").length.toString();
    }
};

const setCheckboxRecursively = (pageId: number, checked: boolean) => {
    const page = document.getElementById(`page-${pageId}`);
    const checkbox = page.querySelector(".bulk-select-item") as HTMLInputElement;
    checkbox.checked = checked;
    const toggleButton = page.querySelector(".toggle-subpages");
    if (toggleButton) {
        const childrenIds: number[] = JSON.parse(toggleButton.getAttribute("data-page-children"));
        childrenIds.forEach((childId) => setCheckboxRecursively(childId, checked));
    }
};

const setSelectAllCheckboxEventListener = (selectAllCheckbox: HTMLInputElement, selectItems: HTMLInputElement[]) => {
    selectAllCheckbox.classList.remove("cursor-wait");
    selectAllCheckbox.addEventListener("click", () => {
        // Set all checkboxes to the same value as the "select all" checkbox
        selectItems.forEach((checkbox) => {
            /* eslint-disable-next-line no-param-reassign */
            checkbox.checked = selectAllCheckbox.checked;
        });
        updateSelectionCount();
    });

    // Set all checkboxes initially in case the page tree was reloaded
    selectItems.forEach((checkbox) => {
        /* eslint-disable-next-line no-param-reassign */
        checkbox.checked = selectAllCheckbox.checked;
    });
    updateSelectionCount();
};

const setSelectItemCheckboxesEventlisteners = (selectItems: HTMLInputElement[]) => {
    selectItems.forEach((selectItem) => {
        selectItem.classList.remove("cursor-wait");
        selectItem.addEventListener("change", () => {
            // Check if checkbox belongs to a page with subpages
            const pageId = selectItem.getAttribute("value");
            const collapsiblePage = document.querySelector(`.toggle-subpages[data-page-id="${pageId}"]`);
            if (collapsiblePage) {
                const childrenIds: number[] = JSON.parse(collapsiblePage.getAttribute("data-page-children"));
                childrenIds.forEach((childId) => {
                    setCheckboxRecursively(childId, selectItem.checked);
                });
            }
            updateSelectionCount();
        });
    });
};

const setAccessBarPerLanguage = (
    accessField: Element,
    languageSlug: string,
    accessesOverTime: number,
    allAccesses: number
) => {
    const parentElement = accessField as HTMLElement;
    const childElement = parentElement.querySelector(
        `.accesses span[data-language-slug="${languageSlug}"]`
    ) as HTMLElement;
    const languageColor = childElement.getAttribute("data-language-color");
    const languageTitle = childElement.getAttribute("data-language-title");
    const roundedPercentage = ((accessesOverTime / allAccesses) * 100).toFixed(2);
    const width = allAccesses !== 0 ? (accessesOverTime / allAccesses) * 100 : 0;
    childElement.style.backgroundColor = languageColor;
    childElement.style.width = `${String(width)}%`;
    childElement.title = `${languageTitle}: ${accessesOverTime} (${roundedPercentage} %)`;
};

const resetTotalAccessesField = (accessFields: HTMLCollectionOf<Element>, isEmpty: boolean) => {
    if (isEmpty) {
        Array.from(accessFields).forEach((accessField) => {
            const allAccessesField = Array.from(accessField.parentElement?.children || []).find(
                (el) => el !== accessField && el.classList.contains("total-accesses")
            );
            const editableAllAccessField = allAccessesField;
            editableAllAccessField.textContent = `${editableAllAccessField.getAttribute("data-translation-no-accesses")}`;
        });
    }
};

const updateAllAccessesField = (accessesField: Element, allAccesses: number) => {
    const allAccessesField = accessesField;
    if (allAccesses === 0) {
        allAccessesField.textContent = allAccessesField.getAttribute("data-translation-no-accesses");
    } else if (allAccesses === 1) {
        allAccessesField.textContent = `${allAccesses} ${allAccessesField.getAttribute("data-translation-singular")}`;
    } else {
        allAccessesField.textContent = `${allAccesses} ${allAccessesField.getAttribute("data-translation-plural")}`;
    }
};

const toggleElementCollection = (elements: HTMLCollectionOf<Element>, show: boolean) => {
    Array.from(elements).forEach((el) => el.classList.toggle("hidden", !show));
};

const setDates = () => {
    const unformattedStartDate = (document.getElementById("id_start_date") as HTMLInputElement).value;
    const unformattedEndDate = (document.getElementById("id_end_date") as HTMLInputElement).value;
    document.getElementById("date-range-start").innerHTML = new Date(unformattedStartDate).toLocaleDateString();
    document.getElementById("date-range-end").innerHTML = new Date(unformattedEndDate).toLocaleDateString();
};

const getData = async (visibleDatasetSlugs: string[], requestID: number): Promise<[AjaxResponse, number]> => {
    if (!statisticsForm) {
        return [{} as AjaxResponse, requestID];
    }

    const accessesServerError = document.getElementById("accesses-server-error");
    const formData = new FormData(statisticsForm);
    visibleDatasetSlugs.forEach((slug) => formData.append("language_slugs", slug));

    const parameters: RequestInit = {
        method: "POST",
        body: formData,
    };

    const response = await fetch(pageAccessesURL, parameters);
    if (!response.ok) {
        console.error(`Fetch failed with status ${response.status}`);
        accessesServerError.classList.remove("hidden");
        return [{} as AjaxResponse, requestID];
    }

    const data: AjaxResponse = await response.json();
    return [data, requestID];
};

const getCheckedSlugs = (): string[] => {
    const visibleDatasetSlugs: string[] = [];
    const languageCheckboxes: NodeListOf<HTMLInputElement> = document.querySelectorAll("[data-language-slug]");

    languageCheckboxes.forEach((checkbox: HTMLInputElement) => {
        if (checkbox.checked) {
            const slug = checkbox.getAttribute("data-language-slug");
            visibleDatasetSlugs.push(slug);
        }
    });
    return visibleDatasetSlugs;
};

const updateNode = (
    parentField: Element,
    visibleDatasetSlugs: string[],
    accesses: AccessesPerLanguageAndInTotal,
    allAccesses: number
) => {
    const accessField = parentField.querySelector(".accesses");
    const allAccessesField = parentField.querySelector(".total-accesses");
    const accessFieldChildElements = accessField.querySelectorAll(`.accesses span`);

    accessFieldChildElements.forEach((accessFieldSpan) => {
        const languageSlug = accessFieldSpan.getAttribute("data-language-slug");
        const accessesOverTime =
            visibleDatasetSlugs.includes(languageSlug) && accesses && accesses[languageSlug]
                ? accesses[languageSlug]
                : 0;
        setAccessBarPerLanguage(accessField, languageSlug, accessesOverTime, allAccesses);
    });

    updateAllAccessesField(allAccessesField, allAccesses);
};

const updateDOMRecursivly = (
    data: AjaxResponse,
    visibleDatasetSlugs: string[],
    parentField: Element
): [AccessesPerLanguageAndInTotal, number] => {
    const pageId: string = parentField.id.split("-")[1];
    const accesses: AccessesPerLanguageAndInTotal = data[pageId] ? { ...data[pageId] } : {};
    const returnAccesses: AccessesPerLanguageAndInTotal = data[pageId] ? { ...data[pageId] } : {};
    const collapseSpan: HTMLSpanElement = parentField.querySelector(".toggle-subpages");
    const allAccesses: number = accesses.total_accesses ? accesses.total_accesses : 0;
    let returnAllAccesses: number = allAccesses;
    let expanded: boolean = false;

    if (collapseSpan) {
        const icon = collapseSpan.querySelector("svg");
        expanded = icon.classList.contains("lucide-chevron-down");
        const childrenIds: number[] = JSON.parse(collapseSpan.getAttribute("data-page-children"));

        childrenIds.forEach((childId) => {
            const page = document.getElementById(`page-${childId}`);
            const [childAccesses, childAllAccesses] = updateDOMRecursivly(data, visibleDatasetSlugs, page);
            returnAllAccesses += childAllAccesses;

            if (returnAccesses) {
                visibleDatasetSlugs.forEach((slug) => {
                    const updateChildAccesses = childAccesses && childAccesses[slug] ? childAccesses[slug] : 0;
                    returnAccesses[slug] = (returnAccesses[slug] ? returnAccesses[slug] : 0) + updateChildAccesses;
                });
            }
        });
    }

    if (expanded) {
        updateNode(parentField, visibleDatasetSlugs, accesses, allAccesses);
    } else {
        updateNode(parentField, visibleDatasetSlugs, returnAccesses, returnAllAccesses);
    }
    return [returnAccesses, returnAllAccesses];
};

const updateDOM = (data: AjaxResponse) => {
    const rootPageNodes = document.querySelectorAll(`.root-page`);
    rootPageNodes.forEach((parentField) => {
        updateDOMRecursivly(data, visibleDatasetSlugs, parentField);
    });
};

const updateExportTable = (data: AjaxResponse) => {
    exportTable = [];
    const checkedPages: NodeListOf<HTMLInputElement> = document.querySelectorAll(".bulk-select-item:checked");
    checkedPages.forEach((page: HTMLInputElement) => {
        const exportTableEntry: string[] = [];
        const pageId = page.value;
        const accesses = data[pageId];
        const pageElement = document.getElementById(`page-${pageId}`);
        const pageSlug = pageElement?.querySelector(".title-slug").getAttribute("data-title-slug");
        if (pageElement && pageSlug) {
            // Page Title needs to be utf-8 encoded for btoa to work in exportPageAccessesData()
            const pageSlugEncoded = new TextEncoder().encode(pageSlug);
            let allAccesses: number = 0;

            visibleDatasetSlugs?.forEach((languageSlug, i) => {
                if (accesses && accesses[languageSlug]) {
                    allAccesses += accesses[languageSlug];
                    exportTableEntry[i] = String(accesses[languageSlug]);
                } else {
                    exportTableEntry[i] = "0";
                }
            });
            exportTableEntry[visibleDatasetSlugs.length] = String(allAccesses);
            exportTableEntry.unshift(String.fromCharCode(...pageSlugEncoded));
            exportTableEntry.unshift(pageId);
            exportTable.push(exportTableEntry);
        }
    });
};

/* The main function which updates the accesses */
export const updatePageAccesses = async (): Promise<void> => {
    document.getElementById("accesses-server-error")?.classList.add("hidden");
    document.getElementById("no-page-and-language-selected-error")?.classList.add("hidden");
    document.getElementById("no-page-selected-error")?.classList.add("hidden");
    document.getElementById("no-language-selected-error")?.classList.add("hidden");
    const pageAccessesLoading = document.getElementById("page-accesses-loading");
    pageAccessesLoading.classList.remove("hidden");
    setDates();
    visibleDatasetSlugs = getCheckedSlugs();

    ajaxRequestID += 1;
    const [data, requestID] = await getData(visibleDatasetSlugs, ajaxRequestID);

    const isEmpty = Object.keys(data).length === 0;
    const accessFields = document.getElementsByClassName("accesses");

    toggleElementCollection(accessFields, !isEmpty);
    resetTotalAccessesField(accessFields, isEmpty);
    updateExportTable(data);

    if (!isEmpty && requestID === ajaxRequestID) {
        updateDOM(data);
    }
    pageAccessesLoading.classList.add("hidden");
};

export const downloadFile = (filename: string, content: string) => {
    const downloadLink = document.getElementById("export-download-link");
    downloadLink.setAttribute("href", content);
    downloadLink.setAttribute("download", filename);
    downloadLink.click();
};

const exportPageAccessesData = (): void => {
    const checkedPages: NodeListOf<HTMLInputElement> = document.querySelectorAll(".bulk-select-item:checked");
    const checkedSlugs = getCheckedSlugs();
    if (checkedPages.length === 0 && checkedSlugs.length === 0) {
        document.getElementById("no-page-and-language-selected-error")?.classList.remove("hidden");
    } else if (checkedPages.length === 0) {
        document.getElementById("no-page-selected-error")?.classList.remove("hidden");
    } else if (checkedSlugs.length === 0) {
        document.getElementById("no-language-selected-error")?.classList.remove("hidden");
    } else {
        const exportSelection = document.getElementById("export-statistics") as HTMLSelectElement;
        const exportLabels: string[] = ["ID", "Slug", ...visibleDatasetSlugs, "Total Accesses"];
        const filename = `Integreat ${exportSelection.getAttribute("data-filename-prefix")} - Page Based`;
        // Create matrix with labels in the first row and the hits per page and language in the subsequent rows
        const csvMatrix: string[][] = [exportLabels].concat(exportTable);
        // Join Matrix to a single csv string
        const csvContent = csvMatrix.map((i) => i.join(",")).join("\n");
        downloadFile(`${filename}.csv`, `data:text/csv;charset=utf-8;base64,${btoa(csvContent)}`);
    }
};

export const setPageAccessesEventListeners = () => {
    ajaxRequestID = 0;
    statisticsForm = document.getElementById("statistics-form") as HTMLFormElement;
    pageAccessesForm = document.getElementById("statistics-page-access") as HTMLFormElement;
    if (pageAccessesForm && statisticsForm) {
        const selectAllCheckbox = document.getElementById("bulk-select-all") as HTMLInputElement;
        const selectItems = <HTMLInputElement[]>Array.from(document.getElementsByClassName("bulk-select-item"));
        // Remove cursor-wait from bulk checkboxes now that subpages have been loaded
        document
            .querySelectorAll<HTMLElement>(".bulk-select-item.cursor-wait, #bulk-select-all.cursor-wait")
            .forEach((el) => el.classList.remove("cursor-wait"));
        pageAccessesURL = pageAccessesForm.getAttribute("data-page-accesses-url");

        setSelectAllCheckboxEventListener(selectAllCheckbox, selectItems);
        setSelectItemCheckboxesEventlisteners(selectItems);
        updatePageAccesses();
        statisticsForm.addEventListener("submit", async (event: Event) => {
            // Prevent form submit
            event.preventDefault();
            updatePageAccesses();
        });
        document.getElementById("export-button")?.addEventListener("click", async () => {
            const exportStatistics = document.getElementById("export-statistics") as HTMLSelectElement;
            if (exportStatistics.value === "page-accesses-csv") {
                // Wait for Page Accesses to be updated to ensure up to date export table
                await updatePageAccesses();
                exportPageAccessesData();
            }
        });
    }
};
