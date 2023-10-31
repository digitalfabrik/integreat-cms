import {
    Chart,
    ChartConfiguration,
    CategoryScale,
    LinearScale,
    Tooltip,
    DoughnutController,
    ArcElement,
    Title,
} from "chart.js";

import { getContent } from "../forms/tinymce-init";
import { getCsrfToken } from "../utils/csrf-token";

// Register all components that are being used - the others will be excluded from the final webpack build
// See https://www.chartjs.org/docs/latest/getting-started/integration.html#bundlers-webpack-rollup-etc for details
Chart.register(DoughnutController, ArcElement, CategoryScale, LinearScale, Tooltip, Title);

const updateChart = (chart: Chart, value: number) => {
    const hixMaxValue = 20;
    const hixThresholdGood = 15;
    const hixThresholdOk = 7;

    chart.data.datasets.forEach((dataset) => {
        // Set new data
        /* eslint-disable-next-line no-param-reassign */
        dataset.data = [value, hixMaxValue - value];

        // Set color based on HIX value
        let backgroundColor;
        if (value > hixThresholdGood) {
            backgroundColor = "rgb(74, 222, 128)";
        } else if (value > hixThresholdOk) {
            backgroundColor = "rgb(250, 204, 21)";
        } else {
            backgroundColor = "rgb(239, 68, 68)";
        }
        /* eslint-disable-next-line no-param-reassign */
        dataset.backgroundColor = [backgroundColor, "rgb(220, 220, 220)"];
    });
    // Set Title to current HIX value
    const roundedHixValue = (Math.round(value * 100) / 100).toString();
    /* eslint-disable-next-line no-param-reassign */
    chart.options.plugins.title.text = ["HIX", roundedHixValue];
    chart.update();
};

/* Show a label based on a state defined in hix_widget.html.
 * States are "updated", "outdated", "no-content" and "error" */
const setHixLabelState = (state: string) => {
    document.querySelectorAll("[data-hix-state]").forEach((element) => {
        if (element.getAttribute("data-hix-state") === state) {
            element.classList.remove("hidden");
        } else {
            element.classList.add("hidden");
        }
    });

    // Hide the canvas if an error occurred
    if (state === "error" || state === "no-content") {
        document.getElementById("hix-container").classList.add("hidden");
    } else if (state === "updated") {
        document.getElementById("hix-container").classList.remove("hidden");
    }

    // Hide the button if there is no content or the value is up-to-date
    const updateButton = document.getElementById("btn-update-hix-value");
    if (state === "updated" || state === "no-content") {
        updateButton.classList.add("hidden");
    } else {
        updateButton.classList.remove("hidden");
    }

    // Hide the loading spinner
    document.getElementById("hix-loading")?.classList.add("hidden");
};

const getHixValue = async () => {
    const updateButton = document.getElementById("btn-update-hix-value");
    let result;
    await fetch(updateButton.dataset.url, {
        method: "POST",
        headers: {
            "X-CSRFToken": getCsrfToken(),
        },
        body: JSON.stringify({
            text: getContent(),
        }),
    })
        .then((response) => response.json())
        .then((json) => {
            const labelState = json.error ? "error" : "updated";
            setHixLabelState(labelState);
            result = json.score;
        });
    return result;
};

window.addEventListener("load", async () => {
    // If the page has no diagram, do nothing
    if (!document.getElementById("hix-chart")) {
        return;
    }

    // Define dummy data for empty default chart.
    const dummyData = {
        datasets: [
            {
                data: [0, 0],
                backgroundColor: ["", ""],
                circumference: 180,
                rotation: -90,
            },
        ],
    };

    const chart: Chart = new Chart("hix-chart", {
        type: "doughnut",
        data: dummyData,
        options: {
            plugins: {
                title: {
                    display: true,
                    text: "HIX",
                    position: "bottom",
                    padding: {
                        top: -100,
                    },
                    font: {
                        size: 24,
                    },
                },
            },
            responsive: true,
            cutout: "80%",
            maintainAspectRatio: false,
            hover: { mode: null },
        },
    } as ChartConfiguration);

    const toggleMTCheckboxes = (disabled: boolean) => {
        const checkboxes: NodeListOf<HTMLInputElement> = document.querySelectorAll(
            "#machine-translation-form input[type='checkbox']"
        );
        checkboxes.forEach((checkbox) => {
            const label = document.querySelector(`label[for='${checkbox.id}']`);
            if (disabled) {
                label.classList.add("pointer-events-none");
                checkbox.classList.add("fake-disable");
            } else {
                label.classList.remove("pointer-events-none");
                checkbox.classList.remove("fake-disable");
            }
        });
    };

    // Show or hide the checkboxes for automatic translation depending on the HIX score
    const toggleMTAvailability = (hixValue: number) => {
        const mtForm = document.getElementById("machine-translation-form");
        const hixScoreWarning = document.getElementById("hix-score-warning");
        const minimumHix = parseFloat(mtForm.dataset.minimumHix);

        if (hixValue && hixValue < minimumHix) {
            hixScoreWarning.classList.remove("hidden");
            toggleMTCheckboxes(true);
        } else {
            hixScoreWarning.classList.add("hidden");
            toggleMTCheckboxes(false);
        }
    };

    const initHixValue = async () => {
        if (!getContent().trim()) {
            setHixLabelState("no-content");
            return;
        }

        const initialHixValue =
            parseFloat(document.getElementById("hix-container").dataset.initialHixScore) || (await getHixValue());

        setHixLabelState("updated");
        updateChart(chart, initialHixValue);
        toggleMTAvailability(initialHixValue);
    };

    // Set listener, that checks, if tinyMCE content has changed to update the
    // HIX value status
    document.querySelectorAll("[data-content-changed]").forEach((element) => {
        // make sure initHixValue is called only after tinyMCE is initialized
        element.addEventListener("tinyMCEInitialized", initHixValue);
        element.addEventListener("contentChanged", () =>
            setHixLabelState(getContent().trim() ? "outdated" : "no-content")
        );
    });

    // Set listener for update button
    document.getElementById("btn-update-hix-value").addEventListener("click", async (event) => {
        document.getElementById("hix-loading")?.classList.remove("hidden");
        event.preventDefault();
        const newHixValue = await getHixValue();
        updateChart(chart, newHixValue);
        toggleMTAvailability(newHixValue);
    });

    const toggleHixIgnore = async () => {
        const hixIgnore = document.getElementById("id_hix_ignore") as HTMLInputElement;
        const hixBlock = document.getElementById("hix-block");
        const mtForm = document.getElementById("machine-translation-form");
        if (hixIgnore.checked) {
            hixBlock.classList.add("hidden");
            toggleMTCheckboxes(true);
            mtForm?.classList.add("hidden");
        } else {
            toggleMTCheckboxes(false);
            mtForm?.classList.remove("hidden");
            hixBlock.classList.remove("hidden");
        }
    };

    // Set listener to show/hide HIX widget when hix_ignore checkbox is clicked
    document.getElementById("id_hix_ignore")?.addEventListener("change", toggleHixIgnore);
    toggleHixIgnore();
});
