export type AjaxResponse = {
    pageId: number;
    accesses: object;
};

export type Access = {
    languageSlug: string;
    accessesOverTime: object;
};

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
    const width = allAccesses !== 0 ? Math.floor((accesses / allAccesses) * 100) : 0;
    const languageColorString = `bg-[${languageColor}%]`;
    childElement.classList.add(`w-[${width}%]`);
    childElement.classList.add(languageColorString);
    console.log(languageColor);
};

const updateChart = async (): Promise<void> => {
    // const chart = Chart.instances[0];

    const chartNetworkError = document.getElementById("chart-network-error");
    const chartServerError = document.getElementById("chart-server-error");
    const chartHeavyTrafficError = document.getElementById("chart-heavy-traffic-error");
    const chartLoading = document.getElementById("chart-loading");

    chartNetworkError.classList.add("hidden");
    chartServerError.classList.add("hidden");
    chartHeavyTrafficError.classList.add("hidden");

    let parameters = {};

    const HTTP_STATUS_OK = 200;
    // const HTTP_STATUS_BAD_REQUEST = 400;
    // const HTTP_STATUS_GATEWAY_TIMEOUT = 504;

    const statisticsForm = document.getElementById("statistics-form") as HTMLFormElement;

    // If form exists (which is the case on the statistics page), perform some extra steps
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
                            const accessesOverTime = access[1];
                            allAccesses += countAccesses(accessesOverTime);
                        });
                        editableAllAccessField.textContent = `${String(allAccesses)} ${editableAllAccessField.getAttribute("data-translation")}`;
                        Object.entries(accesses).forEach((access) => {
                            const languageSlug = access[0];
                            const accessesOverTime = access[1];
                            setAccessesPerLanguage(accessField, languageSlug, accessesOverTime, allAccesses);
                        });
                    }
                });
                // console.log(data)
            });
        }
    } catch (error) {
        console.error("Network error during fetch:", error);
        chartNetworkError.classList.remove("hidden");
    } finally {
        chartLoading.classList.add("hidden");
    }
};

window.addEventListener("load", async () => {
    updateChart();
});
