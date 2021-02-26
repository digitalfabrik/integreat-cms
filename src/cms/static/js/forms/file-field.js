/**
 * This file improves the UI of the image fields by showing the current filename
 */

var inputs = document.querySelectorAll('.image-field');
Array.prototype.forEach.call( inputs, function( input )
{
    var label	 = input.nextElementSibling,
        labelVal = label.textContent;

    input.addEventListener( 'change', function( e )
    {
        var fileName = '';
        fileName = e.target.value.split( '\\' ).pop();

        if( fileName ) {
            label.querySelector('span.standard_text').classList.add('hidden');
            label.querySelector('span.filename').textContent = fileName;
        } else {
            label.querySelector('span.standard_text').classList.remove('hidden');
            label.textContent = labelVal;
        }
    });
});
