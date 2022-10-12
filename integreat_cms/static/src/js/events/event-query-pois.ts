import { create_icons_at } from "../utils/create-icons"
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
    const query_result = document.getElementById("poi-query-result");
    query_result.classList.remove("hidden");
    query_result.innerHTML = data;
    create_icons_at(query_result);
  }

  document.querySelectorAll(".option-new-poi").forEach((node) => {
    node.addEventListener("click", (event) => {
      event.preventDefault();
      newPoiWindow(event);
    });
  });

  document.querySelectorAll(".option-existing-poi").forEach((node) => {
    console.debug("Set event listener for existing POI:", node);
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
    option.getAttribute("data-poi-postcode"),
    option.getAttribute("data-poi-city"),
    option.getAttribute("data-poi-country")
  );
  // Show the address container
  document.getElementById("poi-address-container")?.classList.remove("hidden");
  console.debug("Rendered POI data");
}

function removePoi() {
  renderPoiData(
    document
      .getElementById("poi-query-input")
      .getAttribute("data-default-placeholder"),
    "-1",
    "",
    "",
    "",
    ""
  );
  // Hide the address container
  document.getElementById("poi-address-container")?.classList.add("hidden");
  console.debug("Removed POI data");
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
  postcode: string,
  city: string,
  country: string
) {
  document
    .getElementById("poi-query-input")
    .setAttribute("placeholder", queryPlaceholder);
  document.getElementById("id_location")?.setAttribute("value", id);
  const poiAddress = document.getElementById("poi-address");
  if (poiAddress) {
    poiAddress.textContent = `${address}\n${postcode} ${city}\n${country}`;
  }
  document.getElementById("poi-google-maps-link")
      ?.setAttribute("href", `https://www.google.com/maps/search/?api=1&query=${address}, ${postcode} ${city}, ${country}`)
  document.getElementById("poi-query-result").classList.add("hidden");
  (document.getElementById("poi-query-input") as HTMLInputElement).value = "";
}

let scheduledFunction: number | null = null;
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
      scheduledFunction = window.setTimeout(
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
