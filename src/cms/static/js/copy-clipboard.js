function short_url_to_clipboard(url) {
    var copyText = document.getElementById("copy_to_clipboard");
    var arr = window.location.href.split("/");
    copyText.value = arr[0]+ "//" + arr[2] + "/" + url;
    u('#copy_to_clipboard').removeClass('hidden');
    copyText.select();
    copyText.setSelectionRange(0, 99999);
    document.execCommand("copy");
    u('#copy_to_clipboard').addClass('hidden');
}
