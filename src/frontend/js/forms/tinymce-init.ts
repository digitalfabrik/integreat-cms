import tinymce from "tinymce";

import "tinymce/icons/default";

import "tinymce/themes/silver";
import "tinymce/skins/ui/oxide/skin.css";
import "tinymce/skins/ui/oxide/content.css";
import "tinymce/skins/content/default/content.css";

import "tinymce/plugins/paste";
import "tinymce/plugins/fullscreen";
import "tinymce/plugins/autosave";
import "tinymce/plugins/link";
import "tinymce/plugins/preview";
import "tinymce/plugins/media";
import "tinymce/plugins/image";
import "tinymce/plugins/code";
import "tinymce/plugins/lists";
import "tinymce/plugins/directionality";
import "tinymce/plugins/wordcount";
import "tinymce-i18n/langs/de.js";

import { autosaveEditor } from "./autosave";

function parseSvg(svgUrl: string): string {
  return atob(svgUrl.replace("data:image/svg+xml;base64,", ""));
}

/**
 * This file initializes the tinymce editor.
 */
window.addEventListener("load", () => {
  const tinymceConfig = document.getElementById("tinymce-config-options");

  if (tinymceConfig) {
    tinymce.init({
      selector: ".tinymce_textarea",
      skin: false,
      menubar: "edit view insert format icon",
      menu: {
        icon: {
          title: "Icons",
          items: "pinicon wwwicon callicon clockicon aticon ideaicon",
        },
        format: {
          title: "Format",
          items:
            "bold italic underline strikethrough superscript | formats | forecolor backcolor",
        },
      },
      contextmenu: "paste link",
      autosave_interval: "120s",
      forced_root_block: false,
      plugins:
        "code paste fullscreen autosave link preview media image lists directionality wordcount",
      external_plugins: {
        autolink_tel: "tinymce-plugins/autolink_tel/plugin.js",
      },
      link_default_protocol: "https",
      toolbar:
        "bold italic underline forecolor | bullist numlist | styleselect | undo redo | ltr rtl notranslate | aligncenter indent outdent | link image",
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
            { title: "Code", format: "code" },
          ],
        },
        {
          title: "Blocks",
          items: [
            { title: "Paragraph", format: "p" },
            { title: "Blockquote", format: "blockquote" },
            { title: "Div", format: "div" },
            { title: "Pre", format: "pre" },
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
      min_height: 400,
      content_css: tinymceConfig.getAttribute("data-customcss-src"),
      language: tinymceConfig.getAttribute("data-language"),
      setup: (editor) => {
        editor.ui.registry.addButton("notranslate", {
          tooltip: tinymceConfig.getAttribute("data-notranslate-tooltip"),
          icon: "no_translate",
          onAction: () => {
            editor.focus();
            const val = tinymce.activeEditor.dom.getAttrib(
              tinymce.activeEditor.selection.getNode(),
              "translate",
              "yes"
            );
            if (val == "no") {
              tinymce.activeEditor.dom.setAttrib(
                tinymce.activeEditor.selection.getNode(),
                "translate",
                null
              );
            } else if (editor.selection.getContent().length > 0) {
              editor.selection.setContent(
                '<span class="notranslate" translate="no">' +
                  editor.selection.getContent() +
                  "</span>"
              );
            }
          },
        });
        editor.ui.registry.addIcon(
          "pin_icon",
          parseSvg(require("../../svg/pin.svg").default)
        );
        editor.ui.registry.addIcon(
          "www_icon",
          parseSvg(require("../../svg/world-wide-web.svg").default)
        );
        editor.ui.registry.addIcon(
          "call_icon",
          parseSvg(require("../../svg/call.svg").default)
        );
        editor.ui.registry.addIcon(
          "clock_icon",
          parseSvg(require("../../svg/clock.svg").default)
        );
        editor.ui.registry.addIcon(
          "email_icon",
          parseSvg(require("../../svg/at.svg").default)
        );
        editor.ui.registry.addIcon(
          "idea_icon",
          parseSvg(require("../../svg/idea.svg").default)
        );
        editor.ui.registry.addIcon(
          "no_translate",
          parseSvg(require("../../svg/no_translate.svg").default)
        );
        editor.ui.registry.addMenuItem("pinicon", {
          text: tinymceConfig.getAttribute("data-pinicon-text"),
          icon: "pin_icon",
          onAction: function () {
            editor.insertContent(
              '<img src="' +
                tinymceConfig.getAttribute("data-pinicon-src") +
                '" style="width:15px; height:15px">'
            );
          },
        });
        editor.ui.registry.addMenuItem("wwwicon", {
          text: tinymceConfig.getAttribute("data-wwwicon-text"),
          icon: "www_icon",
          onAction: function () {
            editor.insertContent(
              '<img src="' +
                tinymceConfig.getAttribute("data-wwwicon-src") +
                '" style="width:15px; height:15px">'
            );
          },
        });
        editor.ui.registry.addMenuItem("callicon", {
          text: tinymceConfig.getAttribute("data-callicon-text"),
          icon: "call_icon",
          onAction: function () {
            editor.insertContent(
              '<img src="' +
                tinymceConfig.getAttribute("data-callicon-src") +
                '" style="width:15px; height:15px">'
            );
          },
        });
        editor.ui.registry.addMenuItem("clockicon", {
          text: tinymceConfig.getAttribute("data-clockicon-text"),
          icon: "clock_icon",
          onAction: function () {
            editor.insertContent(
              '<img src="' +
                tinymceConfig.getAttribute("data-clockicon-src") +
                '" style="width:15px; height:15px">'
            );
          },
        });
        editor.ui.registry.addMenuItem("aticon", {
          text: tinymceConfig.getAttribute("data-aticon-text"),
          icon: "email_icon",
          onAction: function () {
            editor.insertContent(
              '<img src="' +
                tinymceConfig.getAttribute("data-aticon-src") +
                '" style="width:15px; height:15px">'
            );
          },
        });
        editor.ui.registry.addMenuItem("ideaicon", {
          text: tinymceConfig.getAttribute("data-ideaicon-text"),
          icon: "idea_icon",
          onAction: function () {
            editor.insertContent(
              '<img src="' +
                tinymceConfig.getAttribute("data-ideaicon-src") +
                '" style="width:15px; height:15px">'
            );
          },
        });
      },
      readonly: !!tinymceConfig.getAttribute("data-readonly"),
      init_instance_callback: function (editor) {
        editor.on("StoreDraft", autosaveEditor);
      },
    });
  }
});
