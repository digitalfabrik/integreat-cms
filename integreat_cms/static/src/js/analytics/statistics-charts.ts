import {
    Chart,
    ChartData,
    LineElement,
    PointElement,
    LineController,
    CategoryScale,
    LinearScale,
    Legend,
    Tooltip,
    LegendItem,
} from "chart.js";
import { setPageAccessesEventListeners, updatePageAccesses } from "./statistics-page-accesses";

export type AjaxResponse = {
    exportLabels: Array<string>;
    chartData: ChartData;
    legend: string;
};

// Register all components that are being used - the others will be excluded from the final webpack build
// See https://www.chartjs.org/docs/latest/getting-started/integration.html#bundlers-webpack-rollup-etc for details
Chart.register(LineElement, PointElement, LineController, CategoryScale, LinearScale, Legend, Tooltip);

// global variable for export labels (better for csv than the readable labels)
let exportLabels: Array<string>;

/*
 * This function toggles a single language in the chart
 */
const toggleSingleChartLanguage = (item: LegendItem, chart: Chart): void => {
    chart.setDatasetVisibility(item.datasetIndex, !chart.isDatasetVisible(item.datasetIndex));
    chart.update();
};

/*
 * This function sets the language legend with the available languages for a region
 */
const setStatisticsLegend = (data: AjaxResponse): void => {
    const legendDiv = document.getElementById("chart-legend-container");
    const legendDivInner = document.getElementById("chart-legend");
    if (legendDiv && legendDivInner) {
        legendDivInner.innerHTML = data.legend;
        legendDiv.classList.remove("hidden");
    }
};

/*
 * This function sets the event listener for selecting all languages at the same time
 */
const setSelectAllLanguagesEventListener = (chart: Chart, items: LegendItem[]): void => {
    const allLanguagesSelected: HTMLInputElement = document.getElementById("select-all-languages") as HTMLInputElement;
    allLanguagesSelected?.addEventListener("change", () => {
        const languageCheckboxes: NodeListOf<HTMLInputElement> = document.querySelectorAll("[data-chart-item]");
        languageCheckboxes.forEach((checkbox: HTMLInputElement) => {
            const editableCheckbox = checkbox;
            if (checkbox.getAttribute("data-language-slug")) {
                editableCheckbox.checked = allLanguagesSelected.checked;
                const dataChartItem = checkbox.getAttribute("data-chart-item");
                const item = items.find((item) => item.text === dataChartItem);
                toggleSingleChartLanguage(item, chart);
                updatePageAccesses();
            }
        });
    });
};

/*
 * This function sets the event listeners for the language legend
 */
const setLegendEventlisteners = (): void => {
    const chart = Chart.instances[0];
    const items = chart.options.plugins.legend.labels.generateLabels(chart);
    items.forEach((item) => {
        const checkbox = document.querySelector(`[data-chart-item="${item.text}"]`);
        checkbox?.addEventListener("change", () => {
            toggleSingleChartLanguage(item, chart);
            if (checkbox.getAttribute("data-language-slug")) {
                updatePageAccesses();
            }
        });
    });
    setSelectAllLanguagesEventListener(chart, items);
};

/*
 * This function updates the chart according to the dates currently selected in the form.
 */
const updateChart = async (): Promise<void> => {
    // Get Chart instance
    const chart = Chart.instances[0];

    // Get HTML elements
    const chartNetworkError = document.getElementById("chart-network-error");
    const chartServerError = document.getElementById("chart-server-error");
    const chartHeavyTrafficError = document.getElementById("chart-heavy-traffic-error");
    const chartLoading = document.getElementById("chart-loading");

    // Hide error in case it was shown before
    chartNetworkError.classList.add("hidden");
    chartServerError.classList.add("hidden");
    chartHeavyTrafficError.classList.add("hidden");

    // Initialize default fetch parameters
    let parameters = {};

    const HTTP_STATUS_OK = 200;
    const HTTP_STATUS_BAD_REQUEST = 400;
    const HTTP_STATUS_GATEWAY_TIMEOUT = 504;

    // Get form
    const statisticsForm = document.getElementById("statistics-form") as HTMLFormElement;

    // If form exists (which is the case on the statistics page), perform some extra steps
    if (statisticsForm) {
        // Get form error elements
        const chartClientErrors = document.getElementsByClassName("chart-client-error");
        // Restore look of potentially incorrect fields
        Array.from(chartClientErrors).forEach((element) => {
            element.classList.add("hidden");
        });
        Array.from(statisticsForm.elements).forEach((element) => {
            element.classList.remove("border-2", "border-red-500");
            element.classList.add("border");
        });
        // define fetch parameters - send POST parameters with form data
        parameters = {
            method: "POST",
            body: new FormData(statisticsForm),
        };
    }

    // Show loading icon
    chartLoading.classList.remove("hidden");

    // Get AJAX URL
    const url = chart.canvas.getAttribute("data-statistics-url");

    try {
        const response = await fetch(url, parameters);

        if (response.status === HTTP_STATUS_OK) {
            // The response text contains the data from Matomo as JSON.
            const data = (await response.json()) as AjaxResponse;
            chart.data = data.chartData;
            chart.update();
            // Save export labels
            exportLabels = data.exportLabels;

            setStatisticsLegend(data);
        } else if (response.status === HTTP_STATUS_BAD_REQUEST) {
            // Client error - invalid form parameters supplied
            const data = await response.json();
            console.error("Invalid form parameters supplied.", data);
            // Mark fields red and show error message
            for (const [fieldId, errors] of Object.entries(data.errors)) {
                const formField = document.getElementById(`id_${fieldId}`);
                formField.classList.remove("border");
                formField.classList.add("border-2", "border-red-500");
                const formFieldError = document.getElementById(`${fieldId}_error`);
                formFieldError.querySelector("span").textContent = errors.toString();
                formFieldError.classList.remove("hidden");
            }
        } else if (response.status === HTTP_STATUS_GATEWAY_TIMEOUT) {
            console.error("Server Error (504):", await response.json());
            chartHeavyTrafficError.classList.remove("hidden");
        } else {
            // Server error - CMS or Matomo server down/malfunctioning
            console.error("Server Error:", await response.json());
            chartServerError.classList.remove("hidden");
        }
    } catch (error) {
        // Network error during fetch
        console.error("Network error during fetch:", error);
        chartNetworkError.classList.remove("hidden");
    } finally {
        // Hide loading icon
        chartLoading.classList.add("hidden");
    }
};

/*
 * This function enables/disables the export button depending on whether an export format is selected or not.
 */
const toggleExportButton = () => {
    // Only activate button if an export format is selected
    const exportFormat = document.getElementById("export-format") as HTMLSelectElement;
    const exportButton = document.getElementById("export-button") as HTMLInputElement;
    if (!exportFormat || !exportButton) {
        return;
    }
    exportButton.disabled = exportFormat.value === "";
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

/*
 * This function exports the current data of the chart into either PNG or CSV.
 */
const exportStatisticsData = (): void => {
    // Get Chart instance
    const chart = Chart.instances[0];
    // Get format select field
    const exportFormat = document.getElementById("export-format") as HTMLSelectElement;
    // Build filename
    const filename = `Integreat ${exportFormat.getAttribute("data-filename-prefix")} ${exportLabels[0]} - ${
        exportLabels[exportLabels.length - 1]
    }`;

    if (exportFormat.value === "image") {
        const timeoutDuration = 300;
        chart.options.plugins.legend.display = true;
        chart.update();

        // Wait till the legend is fully rendered
        setTimeout(() => {
            const ctx = chart.canvas.getContext("2d");

            if (ctx) {
                // This is needed to get a white background for the image. The default background is transparent.
                ctx.globalCompositeOperation = "destination-over";
                ctx.fillStyle = "white";
                ctx.fillRect(0, 0, chart.canvas.width, chart.canvas.height);

                // Capture the chart as a PNG image
                const image = chart.toBase64Image();
                // Initiate download
                downloadFile(`${filename}.png`, image);

                chart.options.plugins.legend.display = false;
                ctx.globalCompositeOperation = "source-over";
                chart.update();
            }
        }, timeoutDuration);
    } else if (exportFormat.value === "csv") {
        // Convert datasets into the format [["language 1", "hits on day 1", "hits 2", ...], [["language 1", "hits on day 1", ...], ...]
        const datasets = chart.data.datasets;
        const datasetsWithLabels: string[][] = datasets
            .filter((dataset) => chart.isDatasetVisible(datasets.indexOf(dataset)))
            .map((dataset) => [dataset.label].concat(dataset.data.map(String)));
        // Ensure export labels don't contain comma and corrupt CSV
        exportLabels = exportLabels.map((x) => x.replace(",", " - "));
        // Create matrix with date labels in the first row and the hits per language in the subsequent rows
        const csvMatrix: string[][] = [[""].concat(exportLabels)].concat(datasetsWithLabels);
        // Transpose matrix (swap rows and columns) and join to a single csv string
        const csvContent = csvMatrix[0].map((col, i) => csvMatrix.map((row) => row[i]).join(",")).join("\n");
        // Initiate download
        downloadFile(`${filename}.csv`, `data:text/csv;charset=utf-8;base64,${btoa(csvContent)}`);
    } else {
        // eslint-disable-next-line no-alert
        alert("Export format is not supported.");
        console.error("Export format not supported");
    }
};

window.addEventListener("load", async () => {
    // If the page has no diagram, do nothing
    if (!document.getElementById("statistics")) {
        return;
    }

    // Initialize chart
    /* eslint-disable-next-line no-new */
    new Chart("statistics", {
        type: "line",
        data: {
            datasets: [],
        },
        options: {
            plugins: {
                legend: {
                    display: false,
                    labels: {
                        usePointStyle: true,
                        pointStyle: "circle",
                    },
                },
                tooltip: {
                    usePointStyle: true,
                },
            },
            scales: {
                y: {
                    beginAtZero: true,
                },
            },
            maintainAspectRatio: false,
        },
    });

    // Initialize chart data
    await updateChart();

    // Set event handlers for page based statistics
    setPageAccessesEventListeners();

    // Set event handlers for language legend
    setLegendEventlisteners();

    // Initialize export button
    toggleExportButton();

    // Set event handler for updating chart
    const statisticsForm = document.getElementById("statistics-form") as HTMLFormElement;
    statisticsForm?.addEventListener("submit", async (event: Event) => {
        // Prevent form submit
        event.preventDefault();
        // Update chart
        await updateChart();
        setLegendEventlisteners();
    });

    // Set event handler for exporting the data
    document.getElementById("export-button")?.addEventListener("click", exportStatisticsData);

    // Event handler for toggling export button
    document.getElementById("export-format")?.addEventListener("change", toggleExportButton);
});
