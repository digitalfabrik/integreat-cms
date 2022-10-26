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
} from "chart.js";

export interface AjaxResponse {
    exportLabels: Array<string>;
    chartData: ChartData;
}

// Register all components that are being used - the others will be excluded from the final webpack build
// See https://www.chartjs.org/docs/latest/getting-started/integration.html#bundlers-webpack-rollup-etc for details
Chart.register(LineElement, PointElement, LineController, CategoryScale, LinearScale, Legend, Tooltip);

// global variable for export labels (better for csv than the readable labels)
let exportLabels: Array<string>;

window.addEventListener("load", async () => {
    // If the page has no diagram, do nothing
    if (!document.getElementById("statistics")) return;

    // Initialize chart
    new Chart("statistics", {
        type: "line",
        data: {
            datasets: [],
        },
        options: {
            scales: {
                y: {
                    beginAtZero: true,
                },
            },
        },
    });

    // Initialize chart data
    await updateChart();

    // Initialize export button
    toggleExportButton();

    // Set event handler for updating chart
    const statisticsForm = document.getElementById("statistics-form") as HTMLFormElement;
    statisticsForm?.addEventListener("submit", async function (event: Event) {
        // Prevent form submit
        event.preventDefault();
        // Update chart
        await updateChart();
    });

    // Set event handler for exporting the data
    document.getElementById("export-button")?.addEventListener("click", exportStatisticsData);

    // Event handler for toggling export button
    document.getElementById("export-format")?.addEventListener("change", toggleExportButton);
});

/*
 * This function updates the chart according to the dates currently selected in the form.
 */
async function updateChart(): Promise<void> {
    // Get Chart instance
    const chart = Chart.instances[0];

    // Get HTML elements
    const chartNetworkError = document.getElementById("chart-network-error");
    const chartServerError = document.getElementById("chart-server-error");
    const chartHeavyTrafficError = document.getElementById("chart-heavy-traffic-error");
    const chartLoading = document.getElementById("chart-loading");
    const chartLabelHelpText = document.getElementById("chart-label-help-text");

    // Hide error in case it was shown before
    chartNetworkError.classList.add("hidden");
    chartServerError.classList.add("hidden");
    chartHeavyTrafficError.classList.add("hidden");

    // Initialize default fetch parameters
    let parameters = {};

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

        if (response.status === 200) {
            // The response text contains the data from Matomo as JSON.
            let data = (await response.json()) as AjaxResponse;
            chart.data = data.chartData;
            chart.update();
            // Save export labels
            exportLabels = data.exportLabels;
            // Show help text
            chartLabelHelpText?.classList.remove("hidden");
        } else if (response.status === 400) {
            // Client error - invalid form parameters supplied
            let data = await response.json();
            console.error("Invalid form parameters supplied.", data);
            // Mark fields red and show error message
            for (let [field_id, errors] of Object.entries(data.errors)) {
                let form_field = document.getElementById("id_" + field_id);
                form_field.classList.remove("border");
                form_field.classList.add("border-2", "border-red-500");
                let form_field_error = document.getElementById(field_id + "_error");
                form_field_error.querySelector("span").textContent = errors.toString();
                form_field_error.classList.remove("hidden");
            }
        } else if (response.status === 504) {
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
}

/*
 * This function enables/disables the export button depending on whether an export format is selected or not.
 */
function toggleExportButton() {
    // Only activate button if an export format is selected
    const exportFormat = document.getElementById("export-format") as HTMLSelectElement;
    const exportButton = document.getElementById("export-button") as HTMLInputElement;
    if (!exportFormat || !exportButton) return;
    exportButton.disabled = exportFormat.value === "";
}

/*
 * This function exports the current data of the chart into either PNG or CSV.
 */
function exportStatisticsData(): void {
    // Get Chart instance
    const chart = Chart.instances[0];
    // Get format select field
    const exportFormat = document.getElementById("export-format") as HTMLSelectElement;
    // Build filename
    let filename =
        "Integreat " +
        exportFormat.getAttribute("data-filename-prefix") +
        " " +
        exportLabels[0] +
        " - " +
        exportLabels[exportLabels.length - 1];

    switch (exportFormat.value) {
        case "image":
            // This is needed to get a white background for the image. The default background is transparent.
            let ctx = chart.canvas.getContext("2d");
            ctx.globalCompositeOperation = "destination-over";
            ctx.fillStyle = "white";
            ctx.fillRect(0, 0, chart.canvas.width, chart.canvas.height);
            // Image Creation of the chart
            let image = chart.toBase64Image();
            // Initiate download
            download_file(filename + ".png", image);
            break;
        case "csv":
            // Convert datasets into the format [["language 1", "hits on day 1", "hits 2", ...], [["language 1", "hits on day 1", ...], ...]
            let datasetsWithLabels: string[][] = chart.data.datasets.map((dataset) =>
                [dataset.label].concat(dataset.data.map(String))
            );
            // Create matrix with date labels in the first row and the hits per language in the subsequent rows
            let csv_matrix: string[][] = [[""].concat(exportLabels)].concat(datasetsWithLabels);
            // Transpose matrix (swap rows and columns) and join to a single csv string
            let csvContent = csv_matrix[0].map((col, i) => csv_matrix.map((row) => row[i]).join(",")).join("\n");
            // Initiate download
            download_file(filename + ".csv", "data:text/csv;charset=utf-8;base64," + btoa(csvContent));
            break;
        default:
            alert("Export format is not supported.");
            console.error("Export format not supported");
    }
}

/*
 * This function initializes a file download by setting the "href" attribute of the download link to the file data
 * and the "download" attribute to the filename.
 * After that, a click on the button is simulated.
 */
function download_file(filename: string, content: string) {
    let downloadLink = document.getElementById("export-download-link");
    downloadLink.setAttribute("href", content);
    downloadLink.setAttribute("download", filename);
    downloadLink.click();
}
