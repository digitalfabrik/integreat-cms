import { Save, Sliders, Folder } from "preact-feather";
import { useEffect, useState } from "preact/hooks";
import { getCsrfToken } from "../../utils/csrf-token";
import { Directory } from "./directory-listing";

interface Props {
  directory: Directory;
  mediaTranslations: any;
  editDirectoryEndpoint: string;
  finishEditSidebar: () => any;
  selectionMode?: boolean;
  globalEdit?: boolean;
}
export default function EditDirectorySidebar({
  directory,
  editDirectoryEndpoint,
  finishEditSidebar,
  selectionMode,
  globalEdit,
  mediaTranslations,
}: Props) {
  const [isLoading, setLoading] = useState(false);
  const [changed_file, setChanged_file] = useState(directory);
  const [success, setSuccess] = useState(false);
  useEffect(() => {
    setChanged_file(directory);
    setSuccess(false);
  }, [directory]);

  const submitChange = async (e: Event) => {
    e.preventDefault();
    setLoading(true);
    try {
      const change_call = await fetch(editDirectoryEndpoint, {
        method: "POST",
        mode: "same-origin",
        credentials: "same-origin",
        headers: {
          "Content-Type": "application/json",
          "X-CSRFToken": getCsrfToken(),
        },
        body: JSON.stringify(changed_file),
      });
      const server_response = await change_call.json();
      if (server_response.success) {
        setSuccess(true);
      }
      finishEditSidebar();
    } catch (error) {
      console.log(error);
    }

    setLoading(false);
  };

  {
    return (
      <div className="w-1/3 rounded-lg border-blue-500 bg-white h-full border-solid shadow-xl">
        <div class="rounded w-full p-4 bg-blue-500 text-white font-bold">
          <Sliders class="mr-1 inline-block h-5" />
          {mediaTranslations.label_directory_properties}
        </div>
        <div class="h-1/3 items-center align-middle w-full">
          <div class="flex h-full items-center">
            <Folder className="w-full h-36 align-middle" />
          </div>
          {success && <div class="text-green-600 text-center">{mediaTranslations.message_suc}</div>}
        </div>
        <form
          onSubmit={submitChange}
          encType="multipart/form-data"
          method="post"
        >
          <div class="p-4 border-b">
            <h2 class="font-bold cursor-pointer">
              {mediaTranslations.label_directory_name}
            </h2>
            <input
              type="text"
              disabled={selectionMode || (!globalEdit && directory.isGlobal)}
              value={changed_file.name}
              onInput={(e) =>
                setChanged_file({
                  ...changed_file,
                  name: (e.target as HTMLInputElement).value,
                })
              }
              class="appearance-none block w-full bg-gray-200 text-xl text-gray-800 border border-gray-200 rounded py-3 px-4 leading-tight focus:outline-none focus:bg-white focus:border-gray-400"
            />
          </div>
          {!selectionMode && (globalEdit || !directory.isGlobal) && (
            <div class="p-4">
              <button
                title={mediaTranslations.btn_save}
                class="confirmation-button w-full bg-blue-500 hover:bg-blue-600 text-white font-bold py-2 px-4 mb-2 rounded"
                type="submit"
              >
                <Save class="mr-1 inline-block h-4" />
                {mediaTranslations.btn_rename}
              </button>
            </div>
          )}
        </form>
      </div>
    );
  }
}
