(function () {
  "use strict";

  var pluginManager = tinymce.util.Tools.resolve("tinymce.PluginManager");

  var global$1 = tinymce.util.Tools.resolve("tinymce.Env");

  const setup = (editor) => {
    const openMediacenter = () => {
      const el = document.createElement("div");
      document.body.append(el);
      const mediaConfigData = JSON.parse(
        document.getElementById("media_config_data").textContent
      );
      window.preactRender(
        window.preactJSX(window.IntegreatSelectMediaDialog, {
          ...mediaConfigData,
          cancel: () => el.remove(),
          selectMedia: (file) => {
            console.debug("File inserted into content:", file);
            el.remove();
            if (file.type.startsWith("image/")) {
              const linkEl = document.createElement("a");
              linkEl.href = file.url;
              const imageEl = document.createElement("img");
              imageEl.src = file.thumbnailUrl;
              imageEl.alt = file.altText;
              linkEl.append(imageEl);
              editor.insertContent(linkEl.outerHTML);
            } else {
              const linkEl = document.createElement("a");
              linkEl.href = file.url;
              linkEl.innerText = file.name;
              editor.insertContent(linkEl.outerHTML);
            }
          },
        }),
        el
      );
    };
    const tinymceConfig = document.getElementById("tinymce-config-options");

    editor.ui.registry.addButton("openmediacenter", {
      text: tinymceConfig.getAttribute("data-media-button-translation"),
      icon: "image",
      onAction: openMediacenter,
    });

    editor.ui.registry.addMenuItem("openmediacenter", {
      text: tinymceConfig.getAttribute("data-media-item-translation"),
      icon: "image",
      onAction: openMediacenter,
    });
  };

  function Plugin() {
    pluginManager.add("mediacenter", function (editor) {
      setup(editor);
    });
  }

  Plugin();
})();
