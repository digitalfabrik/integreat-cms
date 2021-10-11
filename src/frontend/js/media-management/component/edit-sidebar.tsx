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
  Info,
  RefreshCw
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
  onlyImage?: boolean;
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
  onlyImage,
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
        <button class="hidden" disabled={isLoading}></button>
        <div class="flex flex-wrap justify-between gap-2 hover:bg-gray-50 p-4 border-t border-b">
          <label
            for="filename-input"
            className={cn("secondary my-0", {
              "cursor-auto": !isEditingAllowed,
            })}
            onClick={() =>
              isEditingAllowed &&
              !isLoading &&
              setFileNameEditable(!isFileNameEditable)
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
            required
          />
        </div>
        <div class="flex flex-wrap justify-between gap-2 hover:bg-gray-50 p-4 border-b">
          <label
            for="alt-text-input"
            className={cn("secondary my-0", {
              "cursor-auto": !isEditingAllowed,
            })}
            onClick={() =>
              isEditingAllowed &&
              !isLoading &&
              setAltTextEditable(!isAltTextEditable)
            }
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
          />
        </div>
        <div class="flex flex-wrap justify-between gap-2 hover:bg-gray-50 p-4 border-b">
          <label class="secondary my-0">
            {mediaTranslations.label_data_type}
          </label>
          <p>{file.typeDisplay}</p>
        </div>
        <div class="flex flex-wrap justify-between gap-2 hover:bg-gray-50 p-4 border-b">
          <label class="secondary my-0">
            {mediaTranslations.label_file_uploaded}
          </label>
          <p>{file.uploadedDate}</p>
        </div>
        {expertMode && (
          <div class="flex flex-wrap justify-between gap-2 hover:bg-gray-50 p-4 border-b">
            <label class="secondary my-0">{mediaTranslations.label_url}</label>
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
            !(onlyImage && !file.type.startsWith("image/")) ? (
              <button
                title={mediaTranslations.btn_select}
                onClick={(e) => {
                  e.preventDefault();
                  if (selectMedia) {
                    selectMedia(file);
                  }
                }}
                class="w-full"
              >
                {mediaTranslations.btn_select}
              </button>
            ) : (
              <p class="italic">
                <Info class="mr-1 inline-block h-5" />
                {mediaTranslations.text_only_image}
              </p>
            )
          ) : (
            <div>
              {isEditingAllowed ? (
                <div class="flex flex-col gap-4">
                  {(isFileNameEditable || isAltTextEditable) && (
                    <button
                      title={mediaTranslations.btn_save_file}
                      class="btn"
                      disabled={isLoading}
                    >
                      <Save class="inline-block" />
                      {mediaTranslations.btn_save_file}
                    </button>
                  )}

                  <label
                    for="replace-file-input"
                    title={mediaTranslations.btn_replace_file} 
                    className={cn(
                      "w-full text-white text-center font-bold py-3 px-4 m-0 rounded",
                      { "cursor-not-allowed bg-gray-500": isLoading },
                      { "bg-blue-500 hover:bg-blue-600": !isLoading }
                    )}
                    disabled={isLoading} 
                  >
                    <RefreshCw class="mr-1 inline-block h-5" />
                    {mediaTranslations.btn_replace_file}
                  </label>

                  <button
                    title={mediaTranslations.btn_delete_file}
                    class="confirmation-button btn btn-red"
                    data-confirmation-title={
                      mediaTranslations.text_file_delete_confirm
                    }
                    data-confirmation-subject={file.name}
                    data-ajax
                    disabled={isLoading}
                  >
                    <Trash2 class="inline-block" />
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

      {/* Hidden form for file replacement */}
      <form
        onSubmit={submitForm}
        action={apiEndpoints.replaceFile}
        class="hidden"
      >
        <input name="id" type="hidden" value={file.id} />
        <input
          id="replace-file-input"
          name="file"
          type="file"
          maxLength={255}
          accept={file.type}
          disabled={isLoading}
          onChange={
            () => {
              document.getElementById("replace-file").click();
            }
          }
        />
        <button id="replace-file" type="submit"></button>
      </form>

      {/* Hidden form for file deletion (on success, close sidebar) */}
      <form
        onSubmit={submitForm}
        action={apiEndpoints.deleteFile}
        class="hidden"
      >
        <input name="id" type="hidden" value={file.id} />
        <button id="delete-file" />
      </form>
    </div>
  );
}
