u('#icon').on('change', updateIconDisplay);

/**
 * listen for user input (selection in file browser)
 * for uploading region icons
 * updates the icon preview and checkbox for clearing
 */
function updateIconDisplay() {
    const curFiles = u('#icon').first().files;
    if(curFiles.length === 0) {
        u('#icon_status').text("No icon selected");
        u('#clear_icon').addClass("hidden");
        u('#clear_icon').removeClass("block");
    } else {
        u('#icon_status').text(`${curFiles[0].name}`);
        u('#icon_preview').attr({src: URL.createObjectURL(curFiles[0])})
        u('#clear_icon').addClass("block");
        u('#clear_icon').removeClass("hidden");
    }
}