function short_url_to_clipboard(url) {
    let copyDivUmbrella = u('#copy_to_clipboard');
    let copyDivPlain = copyDivUmbrella.first();
    copyDivPlain.value = url;
    copyDivUmbrella.removeClass('hidden');
    copyDivPlain.select();
    copyDivPlain.setSelectionRange(0, 99999);
    document.execCommand("copy");
    copyDivUmbrella.addClass('hidden');
}
