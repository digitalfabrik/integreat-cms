import { getCsrfToken } from "../utils/csrf-token";

window.addEventListener("load", () => {
  if (
    document.getElementById("poi-query-input") &&
    !document.querySelector("[data-disable-poi-query]")
  ) {
    setPoiQueryEventListeners();
    // event handler to reset filter form
    document.getElementById("filter-reset")?.addEventListener("click", removePoi);
  }
});

async function queryPois(
  url: string,
  queryString: string,
  regionSlug: string,
  createPoiOption: boolean
) {
  const response = await fetch(url, {
    method: "POST",
    headers: {
      "X-CSRFToken": getCsrfToken(),
    },
    body: JSON.stringify({
      query_string: queryString,
      region_slug: regionSlug,
      create_poi_option: createPoiOption,
    }),
  });

  if (response.status != 200) {
    // Invalid status => return empty result
    return "";
  }

  const data = await response.text();

  if (data) {
    // Set and display new data
    document.getElementById("poi-query-result").classList.remove("hidden");
    document.getElementById("poi-query-result").innerHTML = data;
  }

  document.querySelectorAll(".option-new-poi").forEach((node) => {
    node.addEventListener("click", (event) => {
      event.preventDefault();
      newPoiWindow(event);
    });
  });

  document.querySelectorAll(".option-existing-poi").forEach((node) => {
    console.debug("add", node);
    node.addEventListener("click", (event) => {
      event.preventDefault();
      setPoi(event);
    });
  });
}

function setPoi({ target }: Event) {
  const option = (target as HTMLElement).closest(".option-existing-poi");
  renderPoiData(
    option.getAttribute("data-poi-title"),
    option.getAttribute("data-poi-id"),
    option.getAttribute("data-poi-address"),
    option.getAttribute("data-poi-city"),
    option.getAttribute("data-poi-country")
  );
}

function removePoi() {
  renderPoiData(
    document
      .getElementById("poi-query-input")
      .getAttribute("data-default-placeholder"),
    "-1",
    "",
    "",
    ""
  );
}

function newPoiWindow({ target }: Event) {
  const option = (target as HTMLElement).closest(".option-new-poi");
  const new_window = window.open(option.getAttribute("data-url"), "_blank");
  new_window.onload = function () {
    new_window.document
      .getElementById("id_title")
      .setAttribute("value", option.getAttribute("data-poi-title"));
  };
}

function renderPoiData(
  queryPlaceholder: string,
  id: string,
  address: string,
  city: string,
  country: string
) {
  document
    .getElementById("poi-query-input")
    .setAttribute("placeholder", queryPlaceholder);
  document.getElementById("id_location")?.setAttribute("value", id);
  document.getElementById("poi-address")?.setAttribute("value", address);
  document.getElementById("poi-city")?.setAttribute("value", city);
  document.getElementById("poi-country")?.setAttribute("value", country);

  document.getElementById("poi-query-result").classList.add("hidden");
  (document.getElementById("poi-query-input") as HTMLInputElement).value = "";
}

let scheduledFunction: number | false = false;
function setPoiQueryEventListeners() {
  // AJAX search
  document
    .getElementById("poi-query-input")
    .addEventListener("keyup", (event) => {
      event.preventDefault();
      const input_field = (event.target as HTMLElement).closest("input");

      // Reschedule function execution on new input
      if (scheduledFunction) {
        clearTimeout(scheduledFunction);
      }
      // Schedule function execution
      scheduledFunction = setTimeout(
        queryPois,
        300,
        input_field.getAttribute("data-url"),
        input_field.value,
        input_field.getAttribute("data-region-slug"),
        !input_field.classList.contains("no-new-poi") // Allow suppressing the option to create a new POI
      );
    });

  // Hide AJAX search results
  document.addEventListener("click", ({ target }) => {
    if (
      !(target as HTMLElement).closest("#poi-query-input") &&
      !(target as HTMLElement).closest("#poi-query-result")
    ) {
      // Neither clicking on input field nor on result to select it
      document.getElementById("poi-query-result").innerHTML = "";
      (document.getElementById("poi-query-input") as HTMLInputElement).value =
        "";
    }
  });

  // Remove POI
  document.getElementById("poi-remove").addEventListener("click", (event) => {
    event.preventDefault();
    removePoi();
  });
}
