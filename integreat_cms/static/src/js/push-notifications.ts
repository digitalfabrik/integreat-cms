window.addEventListener('load', () => {
    document.querySelectorAll('[data-switch-language]').forEach((node) => {
        (node as HTMLElement).addEventListener('click', () => {
            switchLanguage(node.getAttribute('data-switch-language'));
        })
    });
})

function switchLanguage(language: string) {
    document.querySelectorAll('.language-tab-header').forEach((tab) => tab.classList.remove('z-10'));
    document.querySelectorAll('.language-tab-content').forEach((tab) => tab.classList.add('hidden'));
    
    document.getElementById("tab-"+language).classList.remove("hidden");
    document.getElementById("li-"+language).classList.add("z-10");
}

