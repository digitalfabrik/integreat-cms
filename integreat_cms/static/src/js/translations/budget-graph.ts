import { Chart, ChartConfiguration, DoughnutController, ArcElement } from "chart.js";

Chart.register(DoughnutController, ArcElement);

window.addEventListener("load", async () => {
    const graph = document.querySelector("#budget-graph") as HTMLElement;
    if (!graph) {
        return;
    }

    // Display the correct renewal date for the MT budget
    const renewalDateElement = document.querySelector("#deepl-renewal-date") as HTMLElement;
    const renewalMonth = parseInt(renewalDateElement.dataset.renewalMonth, 10);
    const now = new Date();
    // Determine whether or not the next time the renewal month starts will happen this year or next year
    const renewalDate = new Date(
        Date.UTC(now.getFullYear() + (now.getMonth() < renewalMonth ? 0 : 1), renewalMonth, 1)
    );
    renewalDateElement.textContent += renewalDate.toLocaleDateString(undefined, {
        day: "numeric",
        month: "long",
        year: "numeric",
    });

    const budgetUsed = parseInt(graph.dataset.budgetUsed, 10);
    const budgetTotal = parseInt(graph.dataset.budgetTotal, 10);

    const getGraphColor = () => {
        // hue of 0 is red, hue of 128 is green
        const maxHueValue = 128;
        const fractionUsed = budgetUsed / budgetTotal;

        // Return a Hue-Saturation-Luminance string where Hue depends on the used budget
        return `hsl(${(1 - fractionUsed) * maxHueValue}, 100%, 50%)`;
    };

    const data = {
        datasets: [
            {
                data: [budgetUsed, budgetTotal - budgetUsed],
                backgroundColor: [getGraphColor(), "lightgray"],
                circumference: 180,
                rotation: -90,
            },
        ],
    };

    const _: Chart = new Chart("budget-graph", {
        type: "doughnut",
        data,
        options: {
            responsive: true,
            cutout: "80%",
            maintainAspectRatio: false,
            events: [],
        },
    } as ChartConfiguration);
});
