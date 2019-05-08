document.addEventListener('DOMContentLoaded', function(){ 
    tinymce.init({
        selector: '.tinymce_textarea'
    });

    custom_file_field();
}, false);

function custom_file_field() {
    var inputs = document.querySelectorAll('.image-field');
    Array.prototype.forEach.call( inputs, function( input )
    {
        var label	 = input.nextElementSibling,
            labelVal = label.innerHTML;

        input.addEventListener( 'change', function( e )
        {
            var fileName = '';
            fileName = e.target.value.split( '\\' ).pop();

            if( fileName ) {
                label.querySelector('span.standard_text').classList.add('hidden');
                label.querySelector('span.filename').innerHTML = fileName;
            } else {
                label.querySelector('span.standard_text').classList.remove('hidden');
                label.innerHTML = labelVal;
            }
        });
    });
}

function confirmation_popup(e, id) {
    e.preventDefault();
    u('#popup-overlay').removeClass('hidden');
    u(id).removeClass('hidden');
    u(id).addClass('flex');
}

function close_confirmation_popup(e) {
    e.preventDefault();
    u('#popup-overlay').addClass('hidden');
    u('.confirmation-popup').removeClass('flex');
    u('.confirmation-popup').addClass('hidden');
}