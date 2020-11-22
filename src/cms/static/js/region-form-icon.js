// buffer for icon source
var iconSrc;

u('#icon').on('change', updateIconDisplay);

/**
 * listen for user input (selection in file browser)
 * for uploading region icons
 * updates the icon preview and checkbox for clearing
 * @param {Event} event - selected icon changed
 */
function updateIconDisplay(event) {
    const curFiles = u(this).first().files;
    if(curFiles.length === 0) {
        u('#icon_file').addClass("hidden");
        u('#clear_icon').addClass("hidden");
        u('#no_icon').removeClass("hidden");
    } else {
        u('#no_icon').addClass("hidden");
        u('#icon_file').removeClass("hidden");
        u('#icon_file').text(`${curFiles[0].name}`);
        u('#icon_preview').attr({src: URL.createObjectURL(curFiles[0])})
        u('#clear_icon').removeClass("hidden");
        u('#icon-clear_id').first().checked = false;
    }
}

u('#icon-clear_id').on('change', updateIconSelection);

/**
 * handles clear icon checkbox for unselecting the file
 * submitting with enabled checkbox deletes icon on server side
 * @param {Event} event - state of clear checkbox changed
 */
function updateIconSelection(event) {
    if(u(this).is(':checked')) {
        u('#icon_file').addClass("hidden");
        u('#no_icon').removeClass("hidden");
        iconSrc = u('#icon_preview').attr('src');
        u('#icon_preview').attr({src: "https://tailwindcss.com/img/card-top.jpg"});
    } else {
        if (iconSrc && u('#icon_file')) {
            u('#icon_preview').attr({src: iconSrc});
            u('#icon_file').removeClass("hidden");
            u('#no_icon').addClass("hidden");
        }
    }
}

u('form').on('submit', checkInput);

/**
 * make sure that on enabled icon clear checkbox the icon reference
 * of the file input is removed
 * @param {Event} event - emitted when the form is finally send to server
 */
function checkInput(event){
    if(u('#icon-clear_id').is(':checked')) {
        u('#icon').first().value = '';
    }
}
