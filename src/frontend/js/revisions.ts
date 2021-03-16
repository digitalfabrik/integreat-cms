/**
 * This file contains all functions which are needed for the diff calculation of revisions.
 */

import HtmlDiff from "htmldiff-js";

window.addEventListener("load", () => {
  // Iterate over revisions and calculate diff
  document.querySelectorAll(".revision-plain").forEach((revision) => {
    // The div wrapper around plain content and diff
    const parent = revision.parentNode;
    // The numeric id of the revision
    const id = parseInt((parent as HTMLElement).id.substring(9));
    // The plain content div of the previous revision
    let prevRevision = document
      .getElementById("revision-" + (id - 1))
      ?.querySelector(":scope > .revision-plain");
    // Calculate the actual diff and insert into the diff div
    if (parent.querySelector(":scope > .revision-diff")) {
      parent.querySelector(
        ":scope > .revision-diff"
      ).innerHTML = HtmlDiff.execute(
        prevRevision?.innerHTML || "",
        revision.innerHTML
      );
    }
  });

  const revisionSlider = document.getElementById("revision-slider");
  if (revisionSlider) {
    // Add event handler for slider input
    document
      .getElementById("revision-slider")
      .addEventListener("input", (event) => {
        event.preventDefault();
        handleRevisionSliderInput(event);
      });
    // Simulate initial input after page load
    revisionSlider.dispatchEvent(new Event("input"));
  }
});

// function to update the revision info and hide/show the current revision diff
function handleRevisionSliderInput({ target }: Event) {
  const revisionInfo = document.getElementById("revision-info");
  // The current revision
  const currentRevision = Number.parseInt((target as HTMLInputElement).value);
  // The total number of revisions
  const numRevisions = Number.parseInt((target as HTMLInputElement).max);
  // The percentage of the current slider position (left = 0%, right = 100%)
  // If numRevisions == 1, the division results in NaN and the part || 0 converts this case to 0%
  const position = ((currentRevision - 1) / (numRevisions - 1)) * 100 || 0;
  // The last updated date of the revision
  const revisionDate = document
    .getElementById("revision-" + currentRevision)
    .getAttribute("data-date");
  // Update the revision info box
  revisionInfo.textContent =
  `Revision: ${currentRevision}\r\n${revisionDate}`;
  // Calculate position of revision info box to make sure it stays within the area of the slider position
  revisionInfo.style.left = `calc(${position}% + (${125 - position * 2.5}px))`;
  // Hide all other revisions
  document.querySelectorAll(".revision-wrapper").forEach((node) => {
    node.classList.add("hidden");
  });
  // Show the current revision diff
  document
    .getElementById("revision-" + currentRevision)
    .classList.remove("hidden");
}
