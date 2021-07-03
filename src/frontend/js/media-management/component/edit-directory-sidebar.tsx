/*
 * This component renders a sidebar which shows information about the current directory
 * as well as provides the possibility to rename and delete the current directory
 */
import { Save, Sliders, Folder, Edit3, Trash2, Lock } from "preact-feather";
import { useEffect, useState } from "preact/hooks";
import cn from "classnames";

import { refreshAjaxConfirmationHandlers } from "../../confirmation-popups";
import { Directory, MediaApiPaths } from "../index";
import { route } from "preact-router";

interface Props {
  directory: Directory;
  apiEndpoints: MediaApiPaths;
  mediaTranslations: any;
  selectionMode?: boolean;
  globalEdit?: boolean;
  submitForm: (event: Event, successCallback?: (data: any) => void) => void;
  isLoading: boolean;
}
export default function EditDirectorySidebar({
  directory,
  apiEndpoints,
  mediaTranslations,
  selectionMode,
  globalEdit,
  submitForm,
  isLoading,
}: Props) {
  // This state is a buffer for the currently changed directory
  const [changedDirectory, setChangedDirectory] = useState<Directory>(directory);
  // This state determines whether the directory name is currently being edited
  const [isDirectoryNameEditable, setDirectoryNameEditable] = useState<boolean>(false);
  // Editing is allowed if the selection mode is disabled and either global edit is enabled or the directory is not global
  const isEditingAllowed = !selectionMode && (globalEdit || !directory.isGlobal);

  useEffect(() => {
    console.log("Opening sidebar for directory:");
    console.log(directory);
    // Reset changed directory buffer
    setChangedDirectory(directory);
    // Hide input field
    setDirectoryNameEditable(false);
    // Set the function which should be executed when the deletion is confirmed
    refreshAjaxConfirmationHandlers(() => {
      document.getElementById("delete-directory").click();
    });
  }, [directory]);

  {
    return (
      <div className="w-full lg:w-96 2xl:w-120  rounded-lg border-blue-500 bg-white border-solid shadow-xl">
        <div class="rounded w-full p-4 bg-blue-500 text-white font-bold">
          <Sliders class="mr-1 inline-block h-5" />
          {mediaTranslations.heading_directory_properties}
        </div>
        <div class="items-center align-middle w-full">
          <div class="flex items-center">
            <Folder className="w-full h-36 align-middle mt-4" />
          </div>
        </div>
        <form
          onSubmit={submitForm}
          action={apiEndpoints.editDirectory}
          encType="multipart/form-data"
        >
          <input name="id" type="hidden" value={directory.id} />
          <div class="flex flex-wrap justify-between gap-2 hover:bg-gray-50 p-4 border-t border-b">
            <label
              for="directory-name-input"
              className={cn("secondary my-0", { "cursor-auto": !isEditingAllowed })}
              onClick={() =>
                isEditingAllowed && !isLoading && setDirectoryNameEditable(!isDirectoryNameEditable)
              }
            >
              {mediaTranslations.label_directory_name}
            </label>
            {!isDirectoryNameEditable && (
              <p class="break-all">
                {directory.name}
                {isEditingAllowed && (
                  <button
                    class="hover:text-blue-500 ml-1 h-5"
                    onClick={(e) => {
                      e.preventDefault();
                      setDirectoryNameEditable(true);
                    }}
                    disabled={isLoading}
                  >
                    <Edit3 class="inline-block" />
                  </button>
                )}
              </p>
            )}
            <input
              id="directory-name-input"
              name="name"
              type={isDirectoryNameEditable ? "text" : "hidden"}
              value={changedDirectory.name}
              onInput={({ target }) =>
                setChangedDirectory({
                  ...changedDirectory,
                  name: (target as HTMLInputElement).value,
                })
              }
              disabled={isLoading}
              required
            />
          </div>
          <div class="flex flex-wrap justify-between gap-2 hover:bg-gray-50 p-4 border-b">
            <label class="secondary my-0">{mediaTranslations.label_directory_created}</label>
            <p>{directory.CreatedDate}</p>
          </div>
          {!selectionMode && (
            <div class="p-4">
              {isEditingAllowed ? (
                <div>
                  {isDirectoryNameEditable && (
                    <button
                      title={mediaTranslations.btn_rename_directory}
                      className={cn(
                        "w-full text-white font-bold py-2 px-4 mb-4 rounded",
                        { "cursor-not-allowed bg-gray-500": isLoading },
                        { "bg-blue-500 hover:bg-blue-600": !isLoading }
                      )}
                      type="submit"
                      disabled={isLoading}
                    >
                      <Save class="mr-1 inline-block h-5" />
                      {mediaTranslations.btn_rename_directory}
                    </button>
                  )}
                  <button
                    title={`${
                      directory.numberOfEntries === 0
                        ? mediaTranslations.btn_delete_directory
                        : mediaTranslations.btn_delete_empty_directory
                    }`}
                    className={cn(
                      "confirmation-button w-full text-white font-bold py-2 px-4 rounded",
                      {
                        "cursor-not-allowed bg-gray-500":
                          isLoading || directory.numberOfEntries !== 0,
                      },
                      {
                        "bg-red-500 hover:bg-red-600":
                          !isLoading && directory.numberOfEntries === 0,
                      }
                    )}
                    data-confirmation-title={mediaTranslations.text_dir_delete_confirm}
                    data-confirmation-subject={directory.name}
                    data-ajax
                    disabled={isLoading || directory.numberOfEntries !== 0}
                  >
                    <Trash2 class="mr-2 inline-block h-5" />
                    {mediaTranslations.btn_delete_directory}
                  </button>
                </div>
              ) : (
                <p class="italic">
                  <Lock class="mr-1 inline-block h-5" />
                  {mediaTranslations.text_dir_readonly}
                </p>
              )}
            </div>
          )}
        </form>
        {/* Hidden form for directory deletion (on success, redirect to parent directory) */}
        <form
          onSubmit={(event: Event) =>
            submitForm(event, () => route(`${directory.parentId && "/"}${directory.parentId}/`))
          }
          action={apiEndpoints.deleteDirectory}
          class="hidden"
        >
          <input name="id" type="hidden" value={directory.id} />
          <button id="delete-directory" type="submit"></button>
        </form>
      </div>
    );
  }
}
