window.addEventListener("load", () => {
  document.querySelectorAll("[data-copy-to-clipboard]").forEach((node) => {
    node.addEventListener("click", ({ currentTarget }) => {
      const value = (currentTarget as HTMLElement).getAttribute(
        "data-copy-to-clipboard"
      );
      const tmpInput = document.createElement("input");
      tmpInput.type = "text";
      document.body.appendChild(tmpInput);
      tmpInput.value = value;
      tmpInput.select();
      tmpInput.setSelectionRange(0, 99999);

      document.execCommand("copy");
      document.body.removeChild(tmpInput);
    });
  });
});
