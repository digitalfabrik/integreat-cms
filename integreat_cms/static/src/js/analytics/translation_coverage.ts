import { Chart, ChartData, BarElement, BarController, CategoryScale, LinearScale, Legend, Tooltip } from "chart.js";

// Register all components that are being used - the others will be excluded from the final webpack build
// See https://www.chartjs.org/docs/latest/getting-started/integration.html#bundlers-webpack-rollup-etc for details
Chart.register(BarElement, BarController, CategoryScale, LinearScale, Legend, Tooltip);

window.addEventListener("load", async () => {
    // If the page has no diagram, do nothing
    if (!document.getElementById("translation_coverage_chart")) {
        return;
    }

    const JsonData: ChartData = JSON.parse(document.getElementById("chart_data").textContent);
    const chart: HTMLElement = document.getElementById("translation_coverage_chart");

    /* eslint-disable-next-line no-new */
    new Chart("translation_coverage_chart", {
        type: "bar",
        data: JsonData,
        options: {
            indexAxis: "y",
            responsive: true,
            scales: {
                x: {
                    stacked: true,
                    title: {
                        display: true,
                        text: chart.getAttribute("data-chart-hits"),
                    },
                },
                y: {
                    stacked: true,
                    title: {
                        display: true,
                        text: chart.getAttribute("data-chart-languages"),
                    },
                },
            },
        },
    });
});
