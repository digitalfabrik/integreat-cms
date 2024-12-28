import { Chart } from "chart.js";

export type AjaxResponse = {
    pageId: number;
    accesses: object;
};

export type Access = {
    languageSlug: string;
    accessesOverTime: object;
};

let chart: Chart | null = null;

const countAccesses = (accessesOverTime: object): number => {
    let accesses: number = 0;
    Object.values(accessesOverTime).forEach((entry) => {
        accesses += entry;
    });
    return accesses;
};

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
    const width = allAccesses !== 0 ? (accesses / allAccesses) * 100 : 0;
    (childElement as HTMLElement).style.backgroundColor = languageColor;
    (childElement as HTMLElement).style.width = `${String(width)}%`;
    (childElement as HTMLElement).title = String(accesses);
};

const hideLoader = () => {
    const loaderIcons = document.getElementsByClassName("page-accesses-loading");
    Array.from(loaderIcons).forEach((loaderIcon) => {
        loaderIcon.classList.add("hidden");
    });
};

const setDates = () => {
    const unformattedStartDate = (document.getElementById("id_start_date") as HTMLInputElement).value;
    const unformattedEndDate = (document.getElementById("id_end_date") as HTMLInputElement).value;
    document.getElementById("date-range-start").innerHTML = new Date(unformattedStartDate).toLocaleDateString();
    document.getElementById("date-range-end").innerHTML = new Date(unformattedEndDate).toLocaleDateString();
};

const updatePageAccesses = async (): Promise<void> => {
    const pageAccessesNetworkError = document.getElementById("page-accesses-network-error");
    const pageAccessesServerError = document.getElementById("page-accesses-server-error");
    const pageAccessesHeavyTrafficError = document.getElementById("page-accesses-heavy-traffic-error");

    pageAccessesNetworkError.classList.add("hidden");
    pageAccessesServerError.classList.add("hidden");
    pageAccessesHeavyTrafficError.classList.add("hidden");

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
            const languageSlugToDatasetId: Map<string, number> = new Map();
            Object.entries(data).forEach((values) => {
                Array.from(accessFields).forEach((accessField) => {
                    const id = values[0];
                    const pageId = accessField.parentElement.getAttribute("id").replace("page-", "");
                    if (id === pageId) {
                        const accesses = values[1];
                        const allAccessesField = Array.from(accessField.parentElement?.children || []).find(
                            (el) => el !== accessField && el.classList.contains("total-accesses")
                        );
                        const editableAllAccessField = allAccessesField;
                        let allAccesses: number = 0;
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
                        Object.entries(accesses).forEach((access) => {
                            const languageSlug = access[0];
                            const accessesOverTime = access[1];
                            if (chart.isDatasetVisible(languageSlugToDatasetId.get(languageSlug))) {
                                setAccessesPerLanguage(accessField, languageSlug, accessesOverTime, allAccesses);
                            } else {
                                setAccessesPerLanguage(accessField, languageSlug, {}, allAccesses);
                            }
                        });
                    }
                });
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
};

window.addEventListener("load", async () => {
    updatePageAccesses();
    chart = Chart.instances[0];
    const oldUpdate = chart.update;
    chart.update = async () => {
        oldUpdate.call(chart);
        updatePageAccesses();
    };
});
