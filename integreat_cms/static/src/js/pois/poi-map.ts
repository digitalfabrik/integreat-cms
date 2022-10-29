import { FullscreenControl, LngLat, LngLatBoundsLike, Map, MapOptions, MapMouseEvent, Marker } from "maplibre-gl";
import { getCsrfToken } from "../utils/csrf-token";
import { updateField } from "./poi-actions";

window.addEventListener("load", () => {
    // Render the map initially
    const [map, marker] = renderMap() as [Map, Marker];

    // Update the map every time a coordinate changes
    const [latitudeInput, longitudeInput] = getCoordinateInputFields();
    latitudeInput.addEventListener("focusout", updateMap.bind(null, map, marker));
    longitudeInput.addEventListener("focusout", updateMap.bind(null, map, marker));

    // Update the address and/or coordinates on confirmation
    document.getElementById("confirm_map_input").addEventListener("click", confirmPositionFields);

    // Just remove the div and render the map with the old data when the discard button is clicked
    document.getElementById("discard_map_input").addEventListener("click", () => {
        hideUpdatePositionForm();
        updateMap(map, marker);
    });
});

// Function to render the map at the current coordinates
function renderMap() {
    // Get the coordinates from the input fields
    const coordinates = getCoordinates();
    let container = document.getElementById("map");

    let options = {
        container: container,
        style: "https://maps.tuerantuer.org/styles/integreat/style.json",
    } as MapOptions;

    if (coordinates) {
        // If coordinates are given, use them as center of the map
        options.center = coordinates;
        options.zoom = 15;
    } else {
        // Else, show a bounding box of the region
        options.bounds = JSON.parse(container.dataset.boundingBox) as LngLatBoundsLike;
    }

    // Initialize map and marker
    let map = new Map(options);
    let marker = new Marker();
    marker.setDraggable(true);

    // If initial coordinates are given, set the marker to this position
    if (coordinates) {
        marker.setLngLat(coordinates).addTo(map);
    }

    // Support setting the marker both via drag & drop and via clicking on the map
    map.on("click", (event: MapMouseEvent) => {
        marker.setLngLat(event.lngLat).addTo(map);
        updateHelpText(event.lngLat);
        fetchAddress(marker);
    });
    marker.on("dragend", () => fetchAddress(marker));

    // Set the initial zoom
    map.on("load", map.resize);

    // Allow to open the map in full screen
    map.addControl(new FullscreenControl({ container: container }));

    updateHelpText(coordinates);

    return [map, marker];
}

// Function to update the map at the current coordinates
function updateMap(map: Map, marker: Marker) {
    // Get the coordinates from the input fields
    const coordinates = getCoordinates();

    if (coordinates) {
        // If coordinates are given, fly to their location
        marker.setLngLat(coordinates).addTo(map);
        map.flyTo({
            center: coordinates,
            zoom: 15,
        });
    } else {
        // Else, remove the marker from the map
        marker.remove();
        // And show a bounding box of the region
        map.fitBounds(JSON.parse(map.getContainer().dataset.boundingBox) as LngLatBoundsLike);
    }

    updateHelpText(coordinates);
}

// Adjust help text below the map
function updateHelpText(coordinates: LngLat) {
    const setMapPositionText = document.getElementById("set_map_position_text");
    const changeMapPositionText = document.getElementById("change_map_position_text");
    if (coordinates) {
        setMapPositionText.classList.add("hidden");
        changeMapPositionText.classList.remove("hidden");
    } else {
        setMapPositionText.classList.remove("hidden");
        changeMapPositionText.classList.add("hidden");
    }
}

// Fetch the address at a given location
async function fetchAddress(marker: Marker) {
    // Show loading spinner
    document.getElementById("address_loading").classList.remove("hidden");
    // Hide error in case it was shown before
    document.getElementById("no_address_found").classList.add("hidden");

    // Get the new coordinates of the marker
    const coordinates = marker.getLngLat();

    // Show new coordinates
    document.getElementById("updated_latitude").textContent = coordinates.lat.toString();
    document.getElementById("updated_longitude").textContent = coordinates.lng.toString();
    document.getElementById("update_position_from_map_marker").classList.remove("hidden");

    // Fetch the address at this coordinates
    const response = await fetch(document.getElementById("map").dataset.url, {
        method: "POST",
        headers: {
            "X-CSRFToken": getCsrfToken(),
        },
        body: JSON.stringify({
            longitude: coordinates.lng,
            latitude: coordinates.lat,
        }),
    });

    // Check if an address could be found
    if (response.status == 200) {
        // Wait for the response
        const data = await response.json();
        // Hide loading spinner
        document.getElementById("address_loading").classList.add("hidden");
        // Show found address
        const street = constructStreet(data.street, data.number);
        const updatedStreet = document.getElementById("updated_street");
        if (street) {
            updatedStreet.textContent = street;
            updatedStreet.classList.remove("hidden");
        } else {
            updatedStreet.textContent = "";
            updatedStreet.classList.add("hidden");
        }
        document.getElementById("updated_postcode").textContent = data.postcode;
        document.getElementById("updated_city").textContent = data.city;
        document.getElementById("updated_country").textContent = data.country;
        document.getElementById("update_address_from_map_marker").classList.remove("hidden");
        // Enable address-related radio buttons
        Array.from(document.getElementsByClassName("depends-on-address")).forEach((element) => {
            element.classList.remove("cursor-not-allowed", "text-gray-500");
            if (element instanceof HTMLInputElement) {
                element.disabled = false;
            }
        });
    } else {
        // Hide loading spinner
        document.getElementById("address_loading").classList.add("hidden");
        // Hide all address-dependent input fields in case they were shown before
        document.getElementById("update_address_from_map_marker").classList.add("hidden");
        // Disable address-related radio buttons
        Array.from(document.getElementsByClassName("depends-on-address")).forEach((element) => {
            element.classList.add("cursor-not-allowed", "text-gray-500");
            if (element instanceof HTMLInputElement) {
                element.disabled = true;
                element.checked = false;
            }
        });
        // Show error
        document.getElementById("no_address_found").classList.remove("hidden");
    }
}

// Construct a single street string from street name and number
function constructStreet(street: string, number: string) {
    // Only append street number if street is given
    if (street && number) {
        return street + " " + number;
    }
    return street;
}

// Get the coordinate input fields
function getCoordinateInputFields() {
    const latitudeInput = document.getElementById("id_latitude") as HTMLInputElement;
    const longitudeInput = document.getElementById("id_longitude") as HTMLInputElement;
    return [latitudeInput, longitudeInput];
}

// Get the values of the coordinate input fields
function getCoordinates() {
    const [latitudeInput, longitudeInput] = getCoordinateInputFields();
    if (latitudeInput.value && longitudeInput.value) {
        return new LngLat(longitudeInput.valueAsNumber, latitudeInput.valueAsNumber);
    }
}

// Set the value of the coordinate input fields to the given value
function updateCoordinates() {
    updateField("latitude", document.getElementById("updated_latitude").textContent);
    updateField("longitude", document.getElementById("updated_longitude").textContent);
}

// Update the address fields to the given values
function updateAddress() {
    updateField("address", document.getElementById("updated_street").textContent);
    updateField("postcode", document.getElementById("updated_postcode").textContent);
    updateField("city", document.getElementById("updated_city").textContent);
    updateField("country", document.getElementById("updated_country").textContent);
}

// Confirm the update of address and/or coordinates via the map pin position
function confirmPositionFields() {
    // Hide error in case it was shown before
    document.getElementById("update_address_error").classList.add("hidden");
    // Determine whether both the address and the coordinates should be updated
    if ((document.getElementById("update_address_and_coordinates") as HTMLInputElement).checked) {
        updateAddress();
        updateCoordinates();
        hideUpdatePositionForm();
    } else if ((document.getElementById("update_address") as HTMLInputElement).checked) {
        updateAddress();
        hideUpdatePositionForm();
    } else if ((document.getElementById("update_coordinates") as HTMLInputElement).checked) {
        updateCoordinates();
        hideUpdatePositionForm();
    } else {
        // If no radio button was clicked, shown an error
        document.getElementById("update_address_error").classList.remove("hidden");
    }
}

// Hide the update form below the map
function hideUpdatePositionForm() {
    document.getElementById("update_position_from_map_marker").classList.add("hidden");
}
