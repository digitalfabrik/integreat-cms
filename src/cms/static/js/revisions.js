/**
 * This file contains all functions which are needed for the diff calculation of revisions.
 * It cannot be included directly, because the npm module htmldiff-js needs to be browserified before it can be used in the browser.
 * Use the following command to bundle this file (this is also automatically executed in dev-tools/run.sh):
 *
 *     npx browserify src/cms/static/js/revisions.js -o src/cms/static/js/revisions_browserified.js -t [ babelify --presets [ @babel/preset-env ] ]
 */

import HtmlDiff from 'htmldiff-js';

// Iterate over revisions and calculate diff
u(".revision-plain").each(function(node, i){
    // The plain content div of the revision
    const revision = u(node);
    // The div wrapper around plain content and diff
    const parent = revision.parent();
    // The numeric id of the revision
    const id = parseInt(parent.attr('id').substring(9));
    // The plain content div of the previous revision
    let prev_revision = u("#revision-" + (id - 1)).children(".revision-plain");
    // Calculate the actual diff and insert into the diff div
    parent.children(".revision-diff").html(HtmlDiff.execute(prev_revision.html(), revision.html()));
});

// Add event handler for slider input
u("#revision-slider").handle("input", handle_revision_slider_input);
// Simulate initial input after page load
u("#revision-slider").trigger("input");

// function to update the revision info and hide/show the current revision diff
function handle_revision_slider_input(event) {
    const revision_info = u("#revision-info").first();
    // The current revision
    const current_revision = event.target.value;
    // The total number of revisions
    const num_revisions = event.target.max;
    // The percentage of the current slider position (left = 0%, right = 100%)
    // If num_revisions == 1, the division results in NaN and the part || 0 converts this case to 0%
    const position = Number(((current_revision - 1) / (num_revisions - 1)) * 100) || 0;
    // The last updated date of the revision
    const revision_date = u("#revision-" + current_revision).data("date");
    // Update the revision info box
    revision_info.innerHTML = "Revision: " + current_revision + "<br>" + revision_date;
    // Calculate position of revision info box to make sure it stays within the area of the slider position
    revision_info.style.left = `calc(${position}% + (${125 - position * 2.5}px))`;
    // Hide all other revisions
    u(".revision-wrapper").each(function(node) {
        u(node).addClass("hidden");
    });
    // Show the current revision diff
    u("#revision-" + current_revision).removeClass("hidden");
}
