import { Parser } from "./shortcodes";
import ContactHandle from "./contact";
import PageHandle from "./page";
import { Registry, ShortcodeHandle } from "./utils";

Registry.register(new PageHandle());
Registry.register(new ContactHandle());

function DummyHandleFactory(keyword) {
    const handle = new ShortcodeHandle();
    handle.keyword = keyword;
    return handle;
}
Registry.setUnknownHandleFactory(DummyHandleFactory);


(() => {
    const tinymceConfig = document.getElementById("tinymce-config-options");
    const parser = new Parser("[", "]", "\\", true, true);
    const context = {
        language: tinymceConfig.getAttribute("data-language"),
        directionality: tinymceConfig.getAttribute("data-directionality"),
    };

    tinymce.PluginManager.add("shortcodes", editor => {
        /*
        function insertShortcode() {
            let html = `<span class="mceNonEditable" data-shortcode="shortcode">[shortcode 2]</span>`;
            editor.insertContent(html);
        }
        */

        editor.on('BeforeSetContent', function(e) {
            /*
            // Ensure all shortcodes are represented by a marker node in tinyMCE
            e.content = e.content.replace(/(<span class="mceNonEditable" data-shortcode="shortcode">\[shortcode (\d+)\]<\/span>|\[shortcode (\d+)\])/g, (match, _, a, b) => {
                return `<span class="mceNonEditable" data-shortcode="shortcode">[shortcode ${a || b}]</span>`;
            });
            */
            console.log("Parsing registered handles:", Registry.instance.handles);
            try {
                e.content = parser.parse(e.content, context);
            } catch (e) {
                console.error("Failed to expand shortcodes:", e);
            }
        });

        editor.on('PreProcess', function(e) {
            // Strip the mce marker out when extracting the content for saving or the source code view
            console.log(`PreProcess – restoring canonical form`, e);
            const shortcodes = Array.from(e.node.querySelectorAll('span.mceNonEditable[data-shortcode]'));
            shortcodes.forEach(node => {
                const keyword = node.dataset.shortcode;
                const handle = Registry.get(keyword);
                node.outerText = handle.renderShortcode(...handle.argsFromNode(node));
            });
        });

        /*
        editor.ui.registry.addMenuItem("add_shortcode", {
            text: "Shortcode",
            icon: "link",
            //shortcut: "Meta+L",
            onAction: insertShortcode,
        });
        */

        Registry.setupAll(editor, parser);

        return {};
    });
})();
