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

const updateDOM = (data: AjaxResponse, visibleDatasetSlugs: string[]) => {
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

/* The main function which updates the accesses */
export const updatePageAccesses = async (): Promise<void> => {
    const pageAccessesLoading = document.getElementById("page-accesses-loading");
    pageAccessesLoading.classList.remove("hidden");
    setDates();
    const visibleDatasetSlugs = getCheckedSlugs();

    ajaxRequestID += 1;
    const [data, requestID] = await getData(visibleDatasetSlugs, ajaxRequestID);

    const isEmpty = Object.keys(data).length === 0;
    const accessFields = document.getElementsByClassName("accesses");

    toggleElementCollection(accessFields, !isEmpty);
    resetTotalAccessesField(accessFields, isEmpty);

    if (!isEmpty && requestID === ajaxRequestID) {
        updateDOM(data, visibleDatasetSlugs);
    }
    pageAccessesLoading.classList.add("hidden");
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
    }
};
