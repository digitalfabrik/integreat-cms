import {
  Chart,
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
window.addEventListener("load", async () => {
  // If the page has no diagram, do nothing
  if (!document.getElementById("hix-chart")) return;

  document.getElementById("hix-loading")?.classList.remove("hidden");

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
      hover: {mode: null},
    },
  });

  // Set listener for update button
  document.getElementById("btn-update-hix-value").addEventListener("click", async (event) => {
    document.getElementById("hix-loading")?.classList.remove("hidden");
    event.preventDefault();
    updateChart(chart, await getHixValue((event.target as HTMLElement).dataset.url));
  });

  // Set listener, that checks, if tinyMCE content has changed to update the
  // HIX value status
  document.querySelectorAll("[data-content-changed]").forEach((element) => {
    element.addEventListener("contentChanged", () => {
      const updateButton = document.getElementById("btn-update-hix-value") as HTMLSelectElement;
      if (!getContent().trim()) {
        updateButton.disabled = true;
        setHixLabelState("no-content");
      } else {
        updateButton.disabled = false;
        setHixLabelState("outdated");
      }
    });
  });

  // Delay the first request, so that tinyMCE can be initialized first
  setTimeout(async () => {
    let updateButton = document.getElementById("btn-update-hix-value") as HTMLSelectElement;
    if (!getContent().trim()) {
      updateButton.disabled = true;
      setHixLabelState("no-content");
      document.getElementById("hix-loading")?.classList.add("hidden");
    } else {
      updateChart(chart, await getHixValue(updateButton.dataset.url));
    }
  }, 1000);
});

function updateChart(chart: Chart, value: number) {
  const hixMaxValue = 20;

  chart.data.datasets.forEach((dataset) => {
    // Set new data
    dataset.data = [value, hixMaxValue - value];

    // Set color based on HIX value
    let backgroundColor;
    if (value > 15) backgroundColor = "rgb(74, 222, 128)";
    else if (value > 7) backgroundColor = "rgb(250, 204, 21)";
    else backgroundColor = "rgb(239, 68, 68)";
    dataset.backgroundColor = [backgroundColor, "rgb(220, 220, 220)"];
  });
  // Set Title to current HIX value
  const roundedHixValue = (Math.round(value * 100) / 100).toString();
  chart.options.plugins.title.text = ["HIX", roundedHixValue];
  chart.update();
}

async function getHixValue(url: string) {
  let result;
  await fetch(url, {
    method: "POST",
    headers: {
      "X-CSRFToken": getCsrfToken(),
    },
    body: JSON.stringify({
      text: getContent(),
    }),
  })
    .then((response) => {
      // Hide loading spinner
      document.getElementById("hix-loading")?.classList.add("hidden");
      return response.json();
    })
    .then((json) => {
      const labelState = json.error ? "error" : "updated";
      setHixLabelState(labelState);
      result = json.score;
    });
  return result;
}

/* Show a label based on a state defined in hix_widget.html.
 * States are "updated", "outdated", "no-content" and "error" */
function setHixLabelState(state: String) {
  document.querySelectorAll("[data-hix-state]").forEach((element) => {
    if (element.getAttribute("data-hix-state") === state) {
      element.classList.remove("hidden");
    } else {
      element.classList.add("hidden");
    }
  });

  // Hide the canvas if an error occurred
  if (state === "error" || state === "no-content") document.getElementById("hix-container").classList.add("hidden");
  else if (state === "updated") document.getElementById("hix-container").classList.remove("hidden");
}
