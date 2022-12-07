import tinymce, { Editor } from "tinymce";

import "tinymce/icons/default";

import "tinymce/themes/silver";

import "tinymce/plugins/fullscreen";
import "tinymce/plugins/autosave";
import "tinymce/plugins/charmap";
import "tinymce/plugins/code";
import "tinymce/plugins/directionality";
import "tinymce/plugins/hr";
import "tinymce/plugins/image";
import "tinymce/plugins/link";
import "tinymce/plugins/lists";
import "tinymce/plugins/media";
import "tinymce/plugins/paste";
import "tinymce/plugins/preview";
import "tinymce/plugins/wordcount";
import "tinymce-i18n/langs/de.js";

import { autosaveEditor } from "./autosave";

export const storeDraft = () => {
    tinymce.activeEditor.plugins.autosave.storeDraft();
};

const parseSvg = (svgUrl: string): string => atob(svgUrl.replace("data:image/svg+xml;base64,", ""));

/* This function adds an icon which can be inserted in the content */
const addIcon = (editor: Editor, tinymceConfig: HTMLElement, name: string): void => {
    /* eslint-disable-next-line @typescript-eslint/no-var-requires, global-require, import/no-dynamic-require */
    editor.ui.registry.addIcon(name, parseSvg(require(`../../svg/${name}.svg`)));
    editor.ui.registry.addMenuItem(name, {
        text: tinymceConfig.getAttribute(`data-${name}-icon-text`),
        icon: name,
        onAction: () => {
            const src = tinymceConfig.getAttribute(`data-${name}-icon-src`);
            editor.insertContent(`<img src="${src}" style="width:15px; height:15px">`);
        },
    });
};

/* This function toggles the no-translate attribute of a selected text */
const toggleNoTranslate = (editor: Editor) => {
    editor.focus();
    const val = tinymce.activeEditor.dom.getAttrib(tinymce.activeEditor.selection.getNode(), "translate", "yes");
    if (val === "no") {
        tinymce.activeEditor.dom.setAttrib(tinymce.activeEditor.selection.getNode(), "translate", null);
    } else if (editor.selection.getContent().length > 0) {
        editor.selection.setContent(`<span class="notranslate" translate="no">${editor.selection.getContent()}</span>`);
    }
};

export const getContent = (): string => tinymce.activeEditor.getContent();

/**
 * This file initializes the tinymce editor.
 */
window.addEventListener("load", () => {
    const tinymceConfig = document.getElementById("tinymce-config-options");

    if (tinymceConfig) {
        tinymce.init({
            selector: ".tinymce_textarea",
            deprecation_warnings: false,
            menubar: "edit view insert format icon",
            menu: {
                edit: {
                    title: "Edit",
                    items: "undo redo | cut copy | selectall",
                },
                icon: {
                    title: "Icons",
                    items: "pin www email call clock idea group",
                },
                format: {
                    title: "Format",
                    items: "bold italic underline strikethrough superscript | formats | forecolor backcolor | notranslate",
                },
                insert: {
                    title: "Insert",
                    items: "openmediacenter add_link media | charmap hr",
                },
            },
            link_title: false,
            autosave_interval: "120s",
            forced_root_block: true,
            plugins: "code fullscreen autosave preview media image lists directionality wordcount hr charmap paste",
            external_plugins: {
                autolink_tel: tinymceConfig.getAttribute("data-custom-plugins"),
                mediacenter: tinymceConfig.getAttribute("data-custom-plugins"),
                custom_link_input: tinymceConfig.getAttribute("data-custom-plugins"),
            },
            link_default_protocol: "https",
            target_list: false,
            default_link_target: "",
            document_base_url: tinymceConfig.getAttribute("data-webapp-url"),
            relative_urls: false,
            remove_script_host: false,
            branding: false,
            paste_as_text: true,
            toolbar:
                "bold italic underline forecolor | bullist numlist | styleselect | undo redo | ltr rtl notranslate | aligncenter indent outdent | link openmediacenter | export | removeformat ",
            style_formats: [
                {
                    title: "Headings",
                    items: [
                        { title: "Heading 2", format: "h2" },
                        { title: "Heading 3", format: "h3" },
                        { title: "Heading 4", format: "h4" },
                        { title: "Heading 5", format: "h5" },
                        { title: "Heading 6", format: "h6" },
                    ],
                },
                {
                    title: "Inline",
                    items: [
                        { title: "Bold", format: "bold" },
                        { title: "Italic", format: "italic" },
                        { title: "Underline", format: "underline" },
                        { title: "Strikethrough", format: "strikethrough" },
                        { title: "Superscript", format: "superscript" },
                        { title: "Subscript", format: "subscript" },
                    ],
                },
                {
                    title: "Align",
                    items: [
                        { title: "Left", format: "alignleft" },
                        { title: "Center", format: "aligncenter" },
                        { title: "Right", format: "alignright" },
                        { title: "Justify", format: "alignjustify" },
                    ],
                },
            ],
            formats: {
                removeformat: [
                    {
                        selector: "b,strong,i,font,u,strike,s,sub,sup,h2,h3,h4,h5,h6",
                        remove: "all",
                        split: true,
                        block_expand: true,
                        expand: false,
                        deep: true,
                    },
                    {
                        selector: "span",
                        attributes: ["style", "class"],
                        remove: "empty",
                        split: true,
                        expand: false,
                        deep: true,
                    },
                    { selector: "*", attributes: ["style", "class"], split: false, expand: false, deep: true },
                ],
            },
            min_height: 400,
            content_css: tinymceConfig.getAttribute("data-content-css"),
            content_style: tinymceConfig.getAttribute("data-content-style"),
            language: tinymceConfig.getAttribute("data-language"),
            directionality: tinymceConfig.getAttribute("data-directionality") as "ltr" | "rtl",
            element_format: "html",
            setup: (editor: Editor) => {
                addIcon(editor, tinymceConfig, "pin");
                addIcon(editor, tinymceConfig, "www");
                addIcon(editor, tinymceConfig, "email");
                addIcon(editor, tinymceConfig, "call");
                addIcon(editor, tinymceConfig, "clock");
                addIcon(editor, tinymceConfig, "idea");
                addIcon(editor, tinymceConfig, "group");
                /* eslint-disable-next-line @typescript-eslint/no-var-requires, global-require */
                editor.ui.registry.addIcon("no-translate", parseSvg(require(`../../svg/no-translate.svg`)));
                editor.ui.registry.addButton("notranslate", {
                    tooltip: tinymceConfig.getAttribute("data-no-translate-tooltip"),
                    icon: "no-translate",
                    onAction: () => toggleNoTranslate(editor),
                });
                editor.ui.registry.addMenuItem("notranslate", {
                    text: tinymceConfig.getAttribute("data-no-translate-text"),
                    icon: "no-translate",
                    onAction: () => toggleNoTranslate(editor),
                });
            },
            readonly: !!tinymceConfig.getAttribute("data-readonly"),
            init_instance_callback: (editor: Editor) => {
                editor.on("StoreDraft", autosaveEditor);
                // When the editor becomes dirty, send an input event, so that the unsaved warning can be shown
                editor.on("dirty", () =>
                    document.querySelectorAll("[data-unsaved-warning]").forEach((element) => {
                        element.dispatchEvent(new Event("input"));
                    })
                );
                // Create an event every time the content changes
                editor.on("keyup", () =>
                    document.querySelectorAll("[data-content-changed]").forEach((element) => {
                        element.dispatchEvent(new Event("contentChanged"));
                    })
                );
            },
        });
    }
});
