function switch_language(language) {
    languages.forEach(function(language){
        u("#tab-"+language).addClass("hidden");
        u("#li-"+language).removeClass("z-10");
    });
    u("#tab-"+language).removeClass("hidden");
    u("#li-"+language).addClass("z-10");
}

