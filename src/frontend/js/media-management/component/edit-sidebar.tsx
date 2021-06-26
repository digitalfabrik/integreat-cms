/*
 * This component renders a sidebar which shows information about the currently
 * active file as well as provides the possibility to modify and delete it
 *
 * Since file deletion is a bit more complex than other functions, the chain of events is explained in detail here:
 *
 *   1. User clicks on delete button
 *   2. Because of the class .confirmation-button, a confirmation popup is opened via showConfirmationPopup()
 *   3. If the user clicks on confirm, the custom event "action-confirmed" is dispatched for the delete button
 *   4. The handler given to refreshAjaxConfirmationHandlers() is executed
 *   5. The file deletion form is submitted by triggering a click on its submit button
 *   6. The onSubmit action of the form is executed
 *   7. submitForm() submits the deletion form via AJAX
 *   8. On success, the media library is refreshed
 */
import { StateUpdater, useEffect, useState } from "preact/hooks";
import {
  FileText,
  Lock,
  Image,
  Save,
  Sliders,
  Trash2,
  XCircle,
  Edit3,
  ExternalLink,
} from "preact-feather";
import cn from "classnames";

import { refreshAjaxConfirmationHandlers } from "../../confirmation-popups";
import { MediaApiPaths, File, MediaLibraryEntry, Directory } from "../index";

interface Props {
  directory: Directory;
  fileIndexState: [number | null, StateUpdater<number | null>];
  directoryContent: MediaLibraryEntry[];
  apiEndpoints: MediaApiPaths;
  mediaTranslations: any;
  selectionMode?: boolean;
  globalEdit?: boolean;
  expertMode?: boolean;
  selectMedia?: (file: File) => any;
  submitForm: (event: Event) => void;
  isLoading: boolean;
}

export default function EditSidebar({
  fileIndexState,
  directoryContent,
  apiEndpoints,
  mediaTranslations,
  selectionMode,
  selectMedia,
  globalEdit,
  expertMode,
  submitForm,
  isLoading,
}: Props) {
  // The file index contains the index of the file which is currently opened in the sidebar
  const [fileIndex, setFileIndex] = fileIndexState;
  // The current directory is the last element of the directory path
  const file = directoryContent[fileIndex] as File;
  // This state is a buffer for the currently changed file
  const [changedFile, setChangedFile] = useState<File>(file);
  // This state determines whether the file name is currently being edited
  const [isFileNameEditable, setFileNameEditable] = useState<boolean>(false);
  // This state determines whether the alternative text of the file is currently being edited
  const [isAltTextEditable, setAltTextEditable] = useState<boolean>(false);
  // Editing is allowed if selection mode is disabled and either global edit is enabled or the file is not global
  const isEditingAllowed = !selectionMode && (globalEdit || !file.isGlobal);

  useEffect(() => {
    console.log("Opening sidebar for file:");
    console.log(file);
    // Reset temporary file buffer
    setChangedFile(file);
    // Hide input fields
    setFileNameEditable(false);
    setAltTextEditable(false);
    // Set the function which should be executed when the deletion is confirmed
    refreshAjaxConfirmationHandlers(() => {
      document.getElementById("delete-file").click();
    });
    return () => {
      console.log("Closing file sidebar...");
    };
  }, [file]);

  return (
    <div className="w-full lg:w-96 2xl:w-120 rounded-lg border-blue-500 shadow-xl bg-white">
      <div class="rounded w-full p-4 bg-blue-500 text-white font-bold">
        <div class="flex flex-row justify-between">
          <span>
            <Sliders class="mr-1 inline-block h-5" />
            {mediaTranslations.heading_file_properties}
          </span>
          <button
            title={mediaTranslations.btn_close}
            class="hover:text-blue-500 hover:bg-white text-white font-bold rounded-full"
            onClick={() => setFileIndex(null)}
          >
            <XCircle class="inline-block h-5 align-text-bottom" />
          </button>
        </div>
      </div>
      <div class="items-center max-w-full">
        {file.thumbnailUrl ? (
          <img src={file.thumbnailUrl} class="max-w-60 m-2 mx-auto"></img>
        ) : file.type.startsWith("image/") ? (
          <Image className="w-full h-36 align-middle mt-4" />
        ) : (
          <FileText className="w-full h-36 align-middle mt-4" />
        )}
      </div>
      <form onSubmit={submitForm} action={apiEndpoints.editFile}>
        <input name="id" type="hidden" value={file.id} />
        {/* Add button which submits the form when the enter-key is pressed (otherwise, the edit-buttons would be triggered) */}
        <button class="hidden" type="submit" disabled={isLoading}></button>
        <div class="flex flex-wrap justify-between gap-2 hover:bg-gray-50 p-4 border-t border-b">
          <label
            for="filename-input"
            className={cn("font-bold", { "cursor-pointer": isEditingAllowed })}
            onClick={() =>
              isEditingAllowed && !isLoading && setFileNameEditable(!isFileNameEditable)
            }
          >
            {mediaTranslations.label_file_name}
          </label>
          {!isFileNameEditable && (
            <p class="break-all">
              {file.name}
              {isEditingAllowed && (
                <button
                  class="hover:text-blue-500 ml-1 h-5"
                  onClick={(e) => {
                    e.preventDefault();
                    setFileNameEditable(true);
                  }}
                  disabled={isLoading}
                >
                  <Edit3 class="inline-block" />
                </button>
              )}
            </p>
          )}
          <input
            id="filename-input"
            name="name"
            type={isFileNameEditable ? "text" : "hidden"}
            value={changedFile.name}
            disabled={isLoading}
            onInput={({ target }) =>
              setChangedFile({
                ...changedFile,
                name: (target as HTMLInputElement).value,
              })
            }
            class="block w-full bg-gray-200 text-xl text-gray-800 border border-gray-200 rounded py-3 px-4 mt-2 leading-tight focus:outline-none focus:bg-white focus:border-gray-400"
            required
          />
        </div>
        <div class="flex flex-wrap justify-between gap-2 hover:bg-gray-50 p-4 border-b">
          <label
            for="alt-text-input"
            className={cn("font-bold", { "cursor-pointer": isEditingAllowed })}
            onClick={() => isEditingAllowed && !isLoading && setAltTextEditable(!isAltTextEditable)}
          >
            {mediaTranslations.label_alt_text}
          </label>
          {!isAltTextEditable && (
            <p class="break-all">
              {file.altText}
              {isEditingAllowed && (
                <button
                  class="hover:text-blue-500 ml-1 h-5"
                  onClick={(e) => {
                    e.preventDefault();
                    setAltTextEditable(true);
                  }}
                  disabled={isLoading}
                >
                  <Edit3 class="inline-block" />
                </button>
              )}
            </p>
          )}
          <input
            id="alt-text-input"
            name="alt_text"
            type={isAltTextEditable ? "text" : "hidden"}
            value={changedFile.altText}
            disabled={isLoading}
            onInput={({ target }) =>
              setChangedFile({
                ...changedFile,
                altText: (target as HTMLInputElement).value,
              })
            }
            class="block w-full bg-gray-200 text-xl text-gray-800 border border-gray-200 rounded py-3 px-4 mt-2 leading-tight focus:outline-none focus:bg-white focus:border-gray-400"
          />
        </div>
        <div class="flex flex-wrap justify-between gap-2 hover:bg-gray-50 p-4 border-b">
          <p class="font-bold">{mediaTranslations.label_data_type}</p>
          <p>{file.typeDisplay}</p>
        </div>
        <div class="flex flex-wrap justify-between gap-2 hover:bg-gray-50 p-4 border-b">
          <p class="font-bold">{mediaTranslations.label_file_uploaded}</p>
          <p>{file.uploadedDate}</p>
        </div>
        {expertMode && (
          <div class="flex flex-wrap justify-between gap-2 hover:bg-gray-50 p-4 border-b">
            <p class="font-bold">{mediaTranslations.label_url}</p>
            <a
              href={file.url}
              target="_blank"
              class="hover:text-blue-500 break-all"
              {...{ native: "" }}
            >
              {file.url}
              <ExternalLink class="inline-block ml-1 h-5" />
            </a>
          </div>
        )}
        <div class="p-4">
          {selectionMode ? (
            <button
              title={mediaTranslations.btn_select}
              onClick={(e) => {
                e.preventDefault();
                if (selectMedia) {
                  selectMedia(file);
                }
              }}
              class="w-full bg-blue-500 hover:bg-blue-600 text-white font-bold py-2 px-4 rounded"
              type="submit"
            >
              {mediaTranslations.btn_select}
            </button>
          ) : (
            <div>
              {isEditingAllowed ? (
                <div>
                  {(isFileNameEditable || isAltTextEditable) && (
                    <button
                      title={mediaTranslations.btn_save_file}
                      className={cn(
                        "w-full text-white font-bold py-2 px-4 mb-4 rounded",
                        { "cursor-not-allowed bg-gray-500": isLoading },
                        { "bg-blue-500 hover:bg-blue-600": !isLoading }
                      )}
                      type="submit"
                      disabled={isLoading}
                    >
                      <Save class="mr-1 inline-block h-5" />
                      {mediaTranslations.btn_save_file}
                    </button>
                  )}
                  <button
                    title={mediaTranslations.btn_delete_file}
                    className={cn(
                      "confirmation-button w-full text-white font-bold py-2 px-4 rounded",
                      { "cursor-not-allowed bg-gray-500": isLoading },
                      { "bg-red-500 hover:bg-red-600": !isLoading }
                    )}
                    data-confirmation-title={mediaTranslations.text_file_delete_confirm}
                    data-confirmation-subject={file.name}
                    data-ajax
                    disabled={isLoading}
                  >
                    <Trash2 class="mr-2 inline-block h-5" />
                    {mediaTranslations.btn_delete_file}
                  </button>
                </div>
              ) : (
                <p class="italic">
                  <Lock class="mr-1 inline-block h-5" />
                  {mediaTranslations.text_file_readonly}
                </p>
              )}
            </div>
          )}
        </div>
      </form>
      {/* Hidden form for file deletion (on success, close sidebar) */}
      <form onSubmit={submitForm} action={apiEndpoints.deleteFile} class="hidden">
        <input name="id" type="hidden" value={file.id} />
        <button id="delete-file" type="submit"></button>
      </form>
    </div>
  );
}
