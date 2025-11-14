import { Chart } from "chart.js";

type AccessesPerLanguage = {
    [lang: string]: number;
};

type AjaxResponse = {
    [id: string]: AccessesPerLanguage;
};

let chart: Chart | null = null;

let statisticsForm: HTMLFormElement;
let pageAccessesURL: string;
let pageAccessesForm: HTMLFormElement;

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

const getData = async (): Promise<AjaxResponse> => {
    if (!statisticsForm) {
        return {} as AjaxResponse;
    }

    const parameters: RequestInit = {
        method: "POST",
        body: new FormData(statisticsForm),
    };

    const response = await fetch(pageAccessesURL, parameters);
    if (!response.ok) {
        console.error(`Fetch failed with status ${response.status}`);
        return {} as AjaxResponse;
    }

    const data: AjaxResponse = await response.json();
    return data;
};

const getAllSlugsFromData = (data: AjaxResponse): Set<string> => {
    const languageSlugs: Set<string> = new Set();

    Object.keys(data).forEach((pageId) => {
        Object.keys(data[pageId]).forEach((languageSlug) => {
            languageSlugs.add(languageSlug);
        });
    });
    return languageSlugs;
};

const createLanguageDatasetLookup = (chart: Chart, slugSet: Set<string>): Map<number, string> => {
    const indexToSlug = new Map<number, string>();

    slugSet.forEach((languageSlug) => {
        const fullLabel = document
            .querySelector(`#chart-legend [data-language-slug="${languageSlug}"]`)
            .getAttribute("data-chart-item");
        const datasetIndex = chart.data.datasets.findIndex((dataset) => dataset.label === fullLabel);
        indexToSlug.set(datasetIndex, languageSlug);
    });

    return indexToSlug;
};

const getVisibleSlugs = (chart: Chart, indexToSlug: Map<number, string>) =>
    chart.data.datasets
        .map((dataset, index) => index)
        .filter((index) => chart.isDatasetVisible(index))
        .map((index) => indexToSlug.get(index))
        .filter((slug) => slug);

const updateDOM = (data: AjaxResponse, visibleDatasetSlugs: string[]) => {
    Object.entries(data).forEach((values) => {
        const pageId: string = values[0];
        const accesses: AccessesPerLanguage = values[1];
        const parentField = document.getElementById(`page-${pageId}`);
        const accessField = parentField.querySelector(".accesses");
        const allAccessesField = parentField.querySelector(".total-accesses");

        let allAccesses: number = 0;
        visibleDatasetSlugs.forEach((languageSlug) => {
            if (accesses[languageSlug]) {
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
        Object.entries(accesses).forEach((accessesForLanguage) => {
            const languageSlug = accessesForLanguage[0];
            const accessesOverTime = visibleDatasetSlugs.includes(languageSlug) ? accessesForLanguage[1] : 0;
            setAccessBarPerLanguage(accessField, languageSlug, accessesOverTime, allAccesses);
        });
    });
};

/* The main function which updates the accesses */
export const updatePageAccesses = async (): Promise<void> => {
    const pageAccessesLoading = document.getElementById("page-accesses-loading");
    pageAccessesLoading.classList.remove("hidden");

    const data = await getData();

    const isEmpty = Object.keys(data).length === 0;
    const accessFields = document.getElementsByClassName("accesses");

    toggleElementCollection(accessFields, !isEmpty);
    resetTotalAccessesField(accessFields, isEmpty);

    if (!isEmpty) {
        const accessedSlugs = getAllSlugsFromData(data);

        const indexToAccessedSlugs = createLanguageDatasetLookup(chart, accessedSlugs);

        const visibleDatasetSlugs: string[] = getVisibleSlugs(chart, indexToAccessedSlugs);

        updateDOM(data, visibleDatasetSlugs);
    }
    pageAccessesLoading.classList.add("hidden");
    setDates();
};

export const setPageAccessesEventListeners = () => {
    statisticsForm = document.getElementById("statistics-form") as HTMLFormElement;
    pageAccessesForm = document.getElementById("statistics-page-access") as HTMLFormElement;
    if (pageAccessesForm && statisticsForm) {
        pageAccessesURL = pageAccessesForm.getAttribute("data-page-accesses-url");
        chart = Chart.getChart("statistics");
        updatePageAccesses();
        statisticsForm.addEventListener("submit", async (event: Event) => {
            // Prevent form submit
            event.preventDefault();
            updatePageAccesses();
        });
    }
};
