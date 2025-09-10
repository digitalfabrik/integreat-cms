(() => {
    const tinymceConfig = document.getElementById("tinymce-config-options");

    tinymce.PluginManager.add("shortcodes", (editor, _url) => {
        function insertShortcode() {
            let html = `<span class="mceNonEditable" data-shortcode="shortcode">[shortcode 2]</span>`;
            editor.insertContent(html);
        }

        editor.on('BeforeSetContent', function(e) {
            // Ensure all shortcodes are represented by a marker node in tinyMCE
            e.content = e.content.replace(/(<span class="mceNonEditable" data-shortcode="shortcode">\[shortcode (\d+)\]<\/span>|\[shortcode (\d+)\])/g, (match, _, a, b) => {
                return `<span class="mceNonEditable" data-shortcode="shortcode">[shortcode ${a || b}]</span>`;
            });
        });

        editor.on('PostProcess', function(e) {
            // Strip the mce marker out when extracting the content for saving or the source code view
            e.content = e.content.replace(/<span class="mceNonEditable" data-shortcode="shortcode">([^<]+)<\/span>/g, '$1');
        });

        editor.ui.registry.addMenuItem("add_shortcode", {
            text: "Shortcode",
            icon: "link",
            //shortcut: "Meta+L",
            onAction: insertShortcode,
        });

        return {};
    });
})();


