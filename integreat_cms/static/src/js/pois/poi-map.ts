import maplibregl from "maplibre-gl";

window.addEventListener("load", () => {
    let longitude = document.getElementById("id_longitude") as HTMLInputElement;
    let latitude = document.getElementById("id_latitude") as HTMLInputElement;

    showPreview();
    longitude.addEventListener("focusout", showPreview);
    latitude.addEventListener("focusout", showPreview);
});

function showPreview() {
    let container = document.getElementById("map");
    let lng = (document.getElementById("id_longitude") as HTMLInputElement).value;
    let lat = (document.getElementById("id_latitude") as HTMLInputElement).value;

    if (lng && lat) {
        document.getElementById("no_coordinates_alert")?.classList.add("hidden");

        let map = new maplibregl.Map({
            container: container, //'map',
            style: "https://maps.tuerantuer.org/styles/integreat/style.json",
            center: [parseFloat(lng), parseFloat(lat)], // starting position [lng, lat]
            zoom: 15, // starting zoom
        });

        let marker = new maplibregl.Marker().setLngLat([parseFloat(lng), parseFloat(lat)]).addTo(map);

        map.on("load", map.resize);
        map.addControl(new maplibregl.FullscreenControl({ container: container }));

        container.classList.remove("hidden");
    } else {
        container.classList.add("hidden");
        document.getElementById("no_coordinates_alert")?.classList.remove("hidden");
    }
}
