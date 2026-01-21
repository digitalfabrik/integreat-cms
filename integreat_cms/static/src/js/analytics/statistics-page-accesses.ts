type AccessesPerLanguage = {
    [lang: string]: number;
};

type AjaxResponse = {
    [id: string]: AccessesPerLanguage;
};

let statisticsForm: HTMLFormElement;
let pageAccessesURL: string;
let pageAccessesForm: HTMLFormElement;
let ajaxRequestID: number;
let exportTable: string[][];
let visibleDatasetSlugs: string[];

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

    const formData = new FormData(statisticsForm);
    visibleDatasetSlugs.forEach((slug) => formData.append("language_slugs", slug));

    const parameters: RequestInit = {
        method: "POST",
        body: formData,
    };

    const response = await fetch(pageAccessesURL, parameters);
    if (!response.ok) {
        console.error(`Fetch failed with status ${response.status}`);
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

const updateDOM = (data: AjaxResponse) => {
    const pageNodes = document.querySelectorAll(`.page-row`);
    pageNodes.forEach((parentField) => {
        const pageId: string = parentField.id.split("-")[1];
        const accesses: AccessesPerLanguage = data[pageId];
        const accessField = parentField.querySelector(".accesses");
        const allAccessesField = parentField.querySelector(".total-accesses");
        const accessFieldChildElements = accessField.querySelectorAll(`.accesses span`);

        let allAccesses: number = 0;
        visibleDatasetSlugs?.forEach((languageSlug) => {
            if (accesses && accesses[languageSlug]) {
                allAccesses += accesses[languageSlug];
            }
        });
        if (allAccesses === 0) {
            allAccessesField.textContent = `${allAccessesField.getAttribute("data-translation-no-accesses")}`;
        } else if (allAccesses === 1) {
            allAccessesField.textContent = `${String(allAccesses)} ${allAccessesField.getAttribute("data-translation-singular")}`;
        } else {
            allAccessesField.textContent = `${String(allAccesses)} ${allAccessesField.getAttribute("data-translation-plural")}`;
        }
        accessFieldChildElements.forEach((child) => {
            const languageSlug = child.getAttribute("data-language-slug");
            const accessesOverTime =
                visibleDatasetSlugs.includes(languageSlug) && accesses && accesses[languageSlug]
                    ? accesses[languageSlug]
                    : 0;
            setAccessBarPerLanguage(accessField, languageSlug, accessesOverTime, allAccesses);
        });
    });
};

const updateExportTable = (data: AjaxResponse) => {
    const pageIds = Object.keys(data);
    exportTable = [];
    pageIds.forEach((pageId) => {
        const exportTableEntry: string[] = [];
        exportTableEntry.push(pageId);
        const accesses = data[pageId];

        let allAccesses: number = 0;
        visibleDatasetSlugs?.forEach((languageSlug) => {
            if (accesses && accesses[languageSlug]) {
                allAccesses += accesses[languageSlug];
                exportTableEntry[visibleDatasetSlugs.indexOf(languageSlug) + 1] = String(accesses[languageSlug]);
            } else {
                exportTableEntry[visibleDatasetSlugs.indexOf(languageSlug) + 1] = "0";
            }
        });
        exportTableEntry[visibleDatasetSlugs.length + 1] = String(allAccesses);
        exportTable.push(exportTableEntry);
    })
}

/* The main function which updates the accesses */
export const updatePageAccesses = async (): Promise<void> => {
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

    if (!isEmpty && requestID === ajaxRequestID) {
        updateDOM(data);
        updateExportTable(data);
    }
    pageAccessesLoading.classList.add("hidden");
};

/*
 * This function initializes a file download by setting the "href" attribute of the download link to the file data
 * and the "download" attribute to the filename.
 * After that, a click on the button is simulated.
 */
const downloadFile = (filename: string, content: string) => {
    const downloadLink = document.getElementById("export-download-link");
    downloadLink.setAttribute("href", content);
    downloadLink.setAttribute("download", filename);
    downloadLink.click();
};

const exportPageAccessesData = (): void => {
    // Get kind of statistics to export. If page access statistics is requested, proceed.
    const exportStatistics = document.getElementById("export-statistics") as HTMLSelectElement;
    if (exportStatistics.value === "page-accesses") {
        // Get format select field
        const exportFormat = document.getElementById("export-format") as HTMLSelectElement;
        if (exportFormat.value === "csv") {
            // Build labels
            const exportLabels: string [] = ["ID"].concat(visibleDatasetSlugs).concat(["Total Accesses"])
            // Build filename
            const filename = `Integreat ${exportFormat.getAttribute("data-filename-prefix")} ${exportLabels[0]} - ${
                exportLabels[exportLabels.length - 1]
            }`;
            // Create matrix with date labels in the first row and the hits per language in the subsequent rows
            const csvMatrix: string[][] = [exportLabels].concat(exportTable);
            // Join Matrix to a single csv string
            const csvContent = csvMatrix.map((i) => i.join(",")).join("\n");
            // Initiate download
            downloadFile(`${filename}.csv`, `data:text/csv;charset=utf-8;base64,${btoa(csvContent)}`);
        } else {
            // eslint-disable-next-line no-alert
            alert("Export format is not supported.");
            console.error("Export format not supported");
        }
    }
};

export const setPageAccessesEventListeners = () => {
    ajaxRequestID = 0;
    statisticsForm = document.getElementById("statistics-form") as HTMLFormElement;
    pageAccessesForm = document.getElementById("statistics-page-access") as HTMLFormElement;
    if (pageAccessesForm && statisticsForm) {
        pageAccessesURL = pageAccessesForm.getAttribute("data-page-accesses-url");
        updatePageAccesses();
        statisticsForm.addEventListener("submit", async (event: Event) => {
            // Prevent form submit
            event.preventDefault();
            updatePageAccesses();
        });
        document.getElementById("export-button")?.addEventListener("click", async () => {
            exportPageAccessesData();
        });
    }
};
