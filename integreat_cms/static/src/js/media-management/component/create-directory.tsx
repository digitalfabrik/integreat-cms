/*
 * This component renders a form to create a new directory
 */
import { route } from "preact-router";
import cn from "classnames";

import { MediaApiPaths } from "../index";
import { FolderPlus } from "preact-feather";
import { StateUpdater } from "preact/hooks";

interface Props {
  parentDirectoryId: string;
  apiEndpoints: MediaApiPaths;
  mediaTranslations: any;
  submitForm: (event: Event, successCallback: (data: any) => void) => void;
  isLoading: boolean;
  setCreateDirectory: StateUpdater<boolean>;
}
export default function CreateDirectory({
  parentDirectoryId,
  apiEndpoints,
  mediaTranslations,
  submitForm,
  isLoading,
  setCreateDirectory,
}: Props) {
  return (
    <div className="flex-auto rounded-lg border-blue-500 shadow-xl bg-white">
      <div class="rounded w-full p-4 bg-blue-500 text-white font-bold">
        <FolderPlus class="inline-block mr-2 h-5" />
        {mediaTranslations.heading_create_directory}
      </div>
      <form
        onSubmit={(event: Event) =>
          // Redirect to new created directory on success
          submitForm(event, (data: any) => {
            setCreateDirectory(false);
            route(`/${data.directory.id}/`);
          })
        }
        action={apiEndpoints.createDirectory}
        className="p-4"
      >
        <input name="parent" type="hidden" value={parentDirectoryId} />
        <label for="create-directory-name-input">
          {mediaTranslations.label_directory_name}
        </label>
        <div class="flex flex-row gap-2 pt-2">
          <input
            id="create-directory-name-input"
            type="text"
            name="name"
            maxLength={255}
            placeholder={mediaTranslations.text_enter_directory_name}
            disabled={isLoading}
            required
          />
          <button
            disabled={isLoading}
            class="btn"
          >
            {mediaTranslations.btn_create}
          </button>
        </div>
      </form>
    </div>
  );
}
