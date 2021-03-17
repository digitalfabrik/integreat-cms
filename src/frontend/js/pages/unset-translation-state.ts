import {getCsrfToken} from "../utils/csrf-token";

interface TranslationState {
  language: string;
}

window.addEventListener("load", () => {
  document
    .querySelectorAll("[data-unset-translation-state]")
    .forEach((unsetTranslationButton) =>
      unsetTranslationButton.addEventListener("click", (event) => {
        event.preventDefault();
        unsetTranslationState(
          unsetTranslationButton.getAttribute(
            "data-unset-translation-state-id"
          ),
          unsetTranslationButton.getAttribute(
            "data-unset-translation-state-language-code"
          )
        );
      })
    );
});

/*
These functions get triggered when user reset the currently_in_translation state
ajax POST request for database update is send, update of translation state icons accordingly
*/
function unsetTranslationState(pageId: string, languageCode: string) {
  // fetch url from template
  const url = document.getElementById("undo-translation").dataset.url;
  const translationState = false;
  // send ajax request for database update
  postTranslationState(url, pageId, languageCode, translationState)
    // on success update GUI
    .then((response) => updateTranslationForm(response));
}

/*
sends ajax request for updating all pages 
to the given translationState
*/
async function postTranslationState(
  url: string,
  pageId: string,
  languageCode: string,
  translationState: boolean
) {
  const response = await fetch(url, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      HTTP_X_REQUESTED_WITH: "XMLHttpRequest",
      "X-CSRFToken": getCsrfToken(),
    },
    body: JSON.stringify({
      language: languageCode,
      pageId: pageId,
      translationState: translationState,
    }),
  });
  return await response.json();
}

function updateTranslationForm(data: TranslationState) {
  /* the icons representing the state of the translation 
    depend on template context at the moment the form was called
    so to update the GUI state, initial state gets hidden and current state is displayed */
  const translationTab = document.querySelector(`.${data.language}`);
  translationTab.classList.add("hidden");
  siblings(translationTab, ".ajax").forEach((node) =>
    node.classList.remove("hidden")
  );
  document.getElementById("trans-warn").classList.add("hidden");
}

function siblings(node: Element, selector: string) {
  const parentNode = node.parentNode;
  return [...parentNode.querySelectorAll(selector)]
    .filter((el) => el.parentNode === parentNode)
    .filter((el) => el !== node);
}
