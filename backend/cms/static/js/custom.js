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

u(document).handle("DOMContentLoaded", function(e) {
    u(".slug-error").closest("#slug-div").addClass("border-red");
});
