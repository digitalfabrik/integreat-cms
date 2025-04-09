import { Chart } from "chart.js";

export type ResponseData = {
    pageId: number;
    accesses: object;
};

export type AjaxResponse = {
    languageLabels: Array<string>;
    responseData: ResponseData;
};

export type Access = {
    languageSlug: string;
    accessesOverTime: object;
};

let chart: Chart | null = null;

// Global variable for language labels for export
let languageLabels: Array<string>;

/* Loop over the object containing the accesses over time and count them to a total */
const countAccesses = (accessesOverTime: object): number => {
    let accesses: number = 0;
    Object.values(accessesOverTime).forEach((entry) => {
        accesses += entry;
    });
    return accesses;
};

/* Set the bar for every language */
const setAccessesPerLanguage = (
    accessField: Element,
    languageSlug: string,
    accessesOverTime: object,
    allAccesses: number
) => {
    const parentElement = accessField as HTMLElement;
    const childElement = parentElement.querySelector(`.accesses span[data-language-slug="${languageSlug}"]`);
    const languageColor = childElement.getAttribute("data-language-color");
    const accesses = countAccesses(accessesOverTime);
    const roundedPercentage = ((accesses / allAccesses) * 100).toFixed(2);
    const width = allAccesses !== 0 ? (accesses / allAccesses) * 100 : 0;
    (childElement as HTMLElement).style.backgroundColor = languageColor;
    (childElement as HTMLElement).style.width = `${String(width)}%`;
    (childElement as HTMLElement).title =
        `${accesses} ${childElement.getAttribute("data-access-translation")} (${roundedPercentage} %)`;
};

/* This function hides the loader icon once the data is there */
const hideLoader = () => {
    const loaderIcons = document.getElementsByClassName("page-accesses-loading");
    Array.from(loaderIcons).forEach((loaderIcon) => {
        loaderIcon.classList.add("hidden");
    });
};

/* Set the selected date at the top of the table */
const setDates = () => {
    const unformattedStartDate = (document.getElementById("id_start_date") as HTMLInputElement).value;
    const unformattedEndDate = (document.getElementById("id_end_date") as HTMLInputElement).value;
    document.getElementById("date-range-start").innerHTML = new Date(unformattedStartDate).toLocaleDateString();
    document.getElementById("date-range-end").innerHTML = new Date(unformattedEndDate).toLocaleDateString();
};

/* The main function which updates the accesses */
const updatePageAccesses = async (): Promise<string[][]> => {
    // Initialize empty array for export data
    const exportTable: string[][] = [];
    const pageAccessesNetworkError = document.getElementById("page-accesses-network-error");

    let parameters = {};

    const HTTP_STATUS_OK = 200;
    const HTTP_STATUS_BAD_REQUEST = 400;
    const HTTP_STATUS_GATEWAY_TIMEOUT = 504;

    const statisticsForm = document.getElementById("statistics-form") as HTMLFormElement;

    if (statisticsForm) {
        parameters = {
            method: "POST",
            body: new FormData(statisticsForm),
        };
    }

    const pageAccessesURL = document.getElementById("statistics-page-access").getAttribute("data-page-accesses-url");
    const accessFields = document.getElementsByClassName("accesses");
    try {
        const response = await fetch(pageAccessesURL, parameters);
        if (response.status === HTTP_STATUS_OK) {
            const data = (await response.json()) as AjaxResponse;
            const responseData = data.responseData as ResponseData;
            // Save language labels for export
            languageLabels = data.languageLabels;
            /* data is the nested response we get from our client. On the first level it contains the page_id and an object.
            This object in itself contains the language_slug and another object. On the third level this object contains the accesses over time with
            a date and the according accesses. */
            const languageSlugToDatasetId: Map<string, number> = new Map();
            Object.entries(responseData).forEach((values) => {
                // We're on the first level of our data. Here we have the page_id and the rest of the object.
                Array.from(accessFields).forEach((accessField) => {
                    const id = values[0];
                    const pageId = accessField.parentElement.getAttribute("id").replace("page-", "");
                    // pageId is the id of a page in our page tree. Id is the id in our data object. In the next line we compare them, to find the right
                    // data for the right row.
                    if (id === pageId) {
                        const accesses = values[1];
                        // We get the column 'total accesses' in our table
                        const allAccessesField = Array.from(accessField.parentElement?.children || []).find(
                            (el) => el !== accessField && el.classList.contains("total-accesses")
                        );
                        const editableAllAccessField = allAccessesField;
                        // Add current page id for export
                        const exportTableEntry: string[] = [];
                        exportTableEntry.push(id)
                        let allAccesses: number = 0;
                        // The next part goes through the subobject and the subobject. It counts the sum of accesses
                        // for all languages and all accesses for the selected timeframe
                        Object.entries(accesses).forEach((access) => {
                            const languageSlug = access[0];
                            if (languageSlugToDatasetId.get(languageSlug) === undefined) {
                                const fullLabel = document
                                    .querySelector(`#chart-legend [data-language-slug="${languageSlug}"]`)
                                    .getAttribute("data-chart-item");
                                const datasetId = chart.data.datasets.findIndex(
                                    (dataset) => dataset.label === fullLabel
                                );
                                languageSlugToDatasetId.set(languageSlug, datasetId);
                            }
                            if (chart.isDatasetVisible(languageSlugToDatasetId.get(languageSlug))) {
                                const accessesOverTime = access[1];
                                allAccesses += countAccesses(accessesOverTime);
                            }
                        });
                        editableAllAccessField.textContent = `${String(allAccesses)} ${editableAllAccessField.getAttribute("data-translation")}`;
                        // Go to the object on the second level. Set the bar of accesses for every language for the selected timeframe.
                        Object.entries(accesses).forEach((access) => {
                            const languageSlug = access[0];
                            let accessesOverTime = access[1];
                            if (chart.isDatasetVisible(languageSlugToDatasetId.get(languageSlug))) {
                                accessesOverTime = countAccesses(accessesOverTime);
                                setAccessesPerLanguage(accessField, languageSlug, accessesOverTime, allAccesses);
                                // Add accesses of current language and page for export
                                exportTableEntry[languageLabels.indexOf(languageSlug) + 1] = String(accessesOverTime);
                            } else {
                                accessesOverTime = countAccesses({});
                                setAccessesPerLanguage(accessField, languageSlug, accessesOverTime, allAccesses);
                                exportTableEntry[languageLabels.indexOf(languageSlug) + 1] = "";
                            }
                        });
                        // Add all accesses of current page for export
                        exportTableEntry[languageLabels.length + 1] = String(allAccesses);
                        exportTable.push(exportTableEntry);
                    }
                });
                // console.log(data)
            });
        } else if (response.status === HTTP_STATUS_BAD_REQUEST) {
            Array.from(accessFields).forEach((accessField) => {
                const editableAllAccessField = accessField;
                editableAllAccessField.textContent = accessField.getAttribute("data-client-error");
            });
        } else if (response.status === HTTP_STATUS_GATEWAY_TIMEOUT) {
            Array.from(accessFields).forEach((accessField) => {
                const editableAllAccessField = accessField;
                editableAllAccessField.textContent = accessField.getAttribute("data-server-error");
            });
        }
    } catch (error) {
        console.error("Network error during fetch:", error);
        pageAccessesNetworkError.classList.remove("hidden");
    } finally {
        hideLoader();
        setDates();
    }
    return exportTable;
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

const exportPageAccessesData = (_exportTable: string[][]): void => {
    // Get kind of statistics to export. If page access statistics is requested, proceed.
    const exportStatistics = document.getElementById("export-statistics") as HTMLSelectElement;
    if (exportStatistics.value === "page-accesses") {
        // Get format select field
        const exportFormat = document.getElementById("export-format") as HTMLSelectElement;
        if (exportFormat.value === "csv") {
            // Build labels
            const exportLabels: string [] = ["ID"].concat(languageLabels).concat(["Total Accesses"])
            // Build filename
            const filename = `Integreat ${exportFormat.getAttribute("data-filename-prefix")} ${exportLabels[0]} - ${
                exportLabels[exportLabels.length - 1]
            }`;
            // Create matrix with date labels in the first row and the hits per language in the subsequent rows
            const csvMatrix: string[][] = [exportLabels].concat(_exportTable);
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

window.addEventListener("load", async () => {
    if (document.getElementById("statistics-page-access")) {
        let exportTable = updatePageAccesses();
        updatePageAccesses();
        chart = Chart.instances[0];
        // Refresh the statistics every time a new timeframe or language is selected
        const oldUpdate = chart.update;
        chart.update = async () => {
            oldUpdate.call(chart);
            exportTable = updatePageAccesses();
        };
        // Set event handler for exporting the data
        document.getElementById("export-button")?.addEventListener("click", async () => {
            exportPageAccessesData(await exportTable);
        });
    }
});
