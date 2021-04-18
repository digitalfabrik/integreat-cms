/*
 * This file contains all functions used for the icon field
 */
import { render } from 'preact';
import SelectMedia from '../media-management/select-media';


// Set event handlers
window.addEventListener("load", () => {
  const iconField = document.getElementById("id_icon");
  const setIconButton = document.getElementById("set-icon-button");
  const removeButton = document.getElementById("remove-icon");
  const restoreButton = document.getElementById("restore-icon");

  if (iconField) {
    iconField.addEventListener("change", updateIconDisplay);
  }
  if (removeButton) {
    removeButton.addEventListener("click", removeIcon);
  }
  if (restoreButton) {
    restoreButton.addEventListener("click", setIcon);
  }
  if (setIconButton) {
    setIconButton.addEventListener("click", setIconwithMediaLibrary);
  }
});

/**
 * Listen for user input (selection in file browser) for uploading icons.
 * Updates the icon preview and UI for clearing.
 *
 * @param event - selected icon changed
 */
function updateIconDisplay({ target }: Event) {
  const files = (target as HTMLInputElement).files;
  // Fill in uploaded file path
  document
    .querySelector("#icon_preview img")
    .setAttribute("src", URL.createObjectURL(files[0]));
  document.getElementById("icon_filename").innerText = files[0].name;
  // Update UI elements
  setIcon();
}

/**
 * Handles all UI elements when an icon is removed
 */
function removeIcon() {
  // Hide preview
  document.getElementById("icon_preview").classList.add("hidden");
  // Change icon label
  document.getElementById("change-icon-label").classList.add("hidden");
  document.getElementById("set-icon-label").classList.remove("hidden");
  // Toggle remove/restore buttons
  document.getElementById("remove-icon").classList.add("hidden");
  document.getElementById("restore-icon").classList.remove("hidden");
  // Set clear-checkbox
  (document.getElementById("icon-clear_id") as HTMLInputElement).checked = true;
}

/**
 * Handles all UI elements when an icon is selected or restored
 */
function setIcon() {
  // Show preview
  document.getElementById("icon_preview").classList.remove("hidden");
  // Change icon label
  document.getElementById("set-icon-label").classList.add("hidden");
  document.getElementById("change-icon-label").classList.remove("hidden");
  // Toggle remove/restore buttons
  document.getElementById("restore-icon").classList.add("hidden");
  document.getElementById("remove-icon").classList.remove("hidden");
  // Unset clear-checkbox
  (document.getElementById(
    "icon-clear_id"
  ) as HTMLInputElement).checked = false;
}



function setIconwithMediaLibrary() {
  const el: HTMLElement = document.createElement("div");
  document.body.append(el);
  const mediaConfigData = JSON.parse(
    document.getElementById("media_config_data").textContent
  );
  render(SelectMedia, {
    ...mediaConfigData,
    cancel: () => el.remove(),
    selectMedia: () => {
      alert();
    },
  el
  });
}