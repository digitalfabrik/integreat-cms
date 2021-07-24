/*
 * This component renders the media library in edit mode,
 * so new directories and files can be added and the existing entries can be modified
 */
import { FilePlus, FolderPlus, Search } from "preact-feather";
import { StateUpdater, useEffect, useState } from "preact/hooks";

import { Directory, MediaApiPaths, MediaLibraryEntry, File } from ".";
import Breadcrumbs from "./component/breadcrumbs";
import DirectoryContent from "./component/directory-content";
import EditDirectorySidebar from "./component/edit-directory-sidebar";
import EditSidebar from "./component/edit-sidebar";
import { Message } from "./component/message";
import CreateDirectory from "./component/create-directory";
import UploadFile from "./component/upload-file";
import { getCsrfToken } from "../utils/csrf-token";

interface Props {
  path: string;
  directoryId?: string;
  loadingState: [boolean, StateUpdater<boolean>];
  showMessage: StateUpdater<Message>;
  apiEndpoints: MediaApiPaths;
  mediaTranslations: any;
  globalEdit?: boolean;
  expertMode?: boolean;
  allowedMediaTypes?: string;
  selectionMode?: boolean;
  onlyImage?: boolean;
  selectMedia?: (file: File) => any;
}

export default function Library({
  path,
  directoryId,
  loadingState,
  showMessage,
  apiEndpoints,
  mediaTranslations,
  globalEdit,
  expertMode,
  allowedMediaTypes,
  selectionMode,
  onlyImage,
  selectMedia,
}: Props) {
  // The directory path contains the current directory and all its parents
  const [directoryPath, setDirectoryPath] = useState<Directory[]>([]);
  // The current directory is the last element of the directory path
  const directory = directoryPath[directoryPath.length - 1];
  // The directory content contains all subdirectories and files of the current directory
  const [directoryContent, setDirectoryContent] = useState<MediaLibraryEntry[]>(
    []
  );
  // The file index contains the index of the file which is currently opened in the sidebar
  const [fileIndex, setFileIndex] = useState<number | null>(null);
  // This state is a semaphore to block actions while an ajax call is running
  const [isLoading, setLoading] = loadingState;
  // This state is used to refresh the media library after changes were made
  const [refresh, setRefresh] = useState<boolean>(false);
  // This state contains a file which should be opened in the sidebar after the content has been refreshed
  const [sidebarFile, setSidebarFile] = useState<File>(null);
  // Whether or not the create directory form should be shown
  const [isCreateDirectory, setCreateDirectory] = useState<boolean>(false);
  // Whether or not the file upload form should be shown
  const [isUploadFile, setUploadFile] = useState<boolean>(false);

  // This submit function is used for all form submissions
  const submitForm = async (
    event: Event,
    successCallback?: (data: any) => void
  ) => {
    event.preventDefault();
    setLoading(true);
    console.log("Submitting form:");
    console.log(event.target);
    let form = event.target as HTMLFormElement;
    try {
      const response = await fetch(form.action, {
        method: "POST",
        headers: {
          "X-CSRFToken": getCsrfToken(),
        },
        body: new FormData(form),
      });
      const data = await response.json();
      if (response.status === 200) {
        console.log("Form submission successful!");
        if (typeof successCallback === "function") {
          console.log("Calling success callback...");
          successCallback(data);
        }
        console.log("Refreshing media library...");
        setRefresh(!refresh);
        if (data.file) {
          setSidebarFile(data.file);
        }
      }
      if (data.messages) {
        data.messages.forEach(showMessage);
      } else if (response.status !== 200) {
        showMessage({
          type: "error",
          text: mediaTranslations.text_error,
        });
      }
    } catch (error) {
      console.log(error);
      showMessage({
        type: "error",
        text: mediaTranslations.text_network_error,
      });
    }
    setLoading(false);
  };

  // This function is used to get information about a directory (either the path or the content)
  const getDirectoryInfo = async (
    url: string,
    directoryId: string,
    successCallback: (data: any) => void
  ) => {
    try {
      const response = await fetch(
        `${url}${directoryId && "?directory="}${directoryId}`
      );
      if (response.status === 200) {
        successCallback((await response.json()).data);
      } else {
        console.log("Server error:");
        console.log(response);
        showMessage({
          type: "error",
          text: mediaTranslations.text_error,
        });
      }
    } catch (error) {
      console.log(error);
      showMessage({
        type: "error",
        text: mediaTranslations.text_network_error,
      });
    }
  };

  // Load the directory path each time the directory id changes
  useEffect(() => {
    if (directoryId) {
      console.log(`Loading directory with id ${directoryId}...`);
    } else {
      console.log(`Loading root directory...`);
    }
    // Load the new directory path
    if (directoryId) {
      getDirectoryInfo(
        apiEndpoints.getDirectoryPath,
        directoryId,
        setDirectoryPath
      );
    } else {
      // The root directory is no real directory object, so the path is empty
      setDirectoryPath([]);
    }
    // Load the new directory content
    getDirectoryInfo(
      apiEndpoints.getDirectoryContent,
      directoryId,
      setDirectoryContent
    );
    // Close the file sidebar
    setFileIndex(null);
  }, [directoryId, refresh]);

  // Open the file in the sidebar after a refresh
  useEffect(() => {
    // Search for the sidebar file in the directory content
    let index = directoryContent.findIndex((x) => x.id === sidebarFile?.id);
    if (index !== -1) {
      console.log("Open changed file in the sidebar again after reload...");
      // Open file in the sidebar
      setFileIndex(index);
      // Reset sidebar buffer
      setSidebarFile(null);
    }
  }, [directoryContent, sidebarFile]);

  // Debug output on directory change
  useEffect(() => {
    if (directory) {
      console.log(`Changed to directory with id ${directoryId}:`);
      console.log(directory);
    } else if (!directoryId) {
      console.log("Changed to root directory");
    }
  }, [directory]);

  return (
    <div className={`flex flex-col flex-grow`}>
      <h1 className="w-full heading p-2">
        {mediaTranslations.heading_media_library}
      </h1>
      <div className="flex flex-wrap justify-between gap-x-2 gap-y-4">
        <form class="table-search relative">
          <Search class="absolute m-2" />
          <input type="search" class="h-full py-2 pl-10 pr-4 rounded shadow" />
        </form>
        {!selectionMode && (globalEdit || !directory?.isGlobal) && (
          <div className="flex flex-wrap justify-start gap-2">
            <button
              title={mediaTranslations.btn_create_directory}
              class="bg-blue-500 hover:bg-blue-600 text-white font-bold py-2 px-4 rounded cursor-pointer"
              onClick={() => setCreateDirectory(!isCreateDirectory)}
            >
              <FolderPlus class="inline-block mr-2 h-5" />
              {mediaTranslations.btn_create_directory}
            </button>
            <button
              title={mediaTranslations.btn_upload_file}
              class="bg-blue-500 hover:bg-blue-600 text-white font-bold py-2 px-4 rounded cursor-pointer"
              onClick={() => setUploadFile(!isUploadFile)}
            >
              <FilePlus class="inline-block mr-2 h-5" />
              {mediaTranslations.btn_upload_file}
            </button>
          </div>
        )}
      </div>
      {(isCreateDirectory || isUploadFile) && (
        <div class="flex flex-row flex-wrap gap-4 mt-4">
          {isCreateDirectory && (
            <CreateDirectory
              parentDirectoryId={directoryId}
              mediaTranslations={mediaTranslations}
              apiEndpoints={apiEndpoints}
              submitForm={submitForm}
              isLoading={isLoading}
              setCreateDirectory={setCreateDirectory}
            />
          )}
          {isUploadFile && (
            <UploadFile
              directory={directory}
              mediaTranslations={mediaTranslations}
              apiEndpoints={apiEndpoints}
              allowedMediaTypes={allowedMediaTypes}
              submitForm={submitForm}
              setUploadFile={setUploadFile}
              isLoading={isLoading}
            />
          )}
        </div>
      )}
      <div className="flex flex-1 flex-col-reverse lg:flex-row gap-4 mt-4">
        <div
          className="flex-1 bg-white border-gray-800 shadow-xl rounded-lg"
          onClick={() => setFileIndex(null)}
        >
          <div class="rounded w-full bg-blue-500 text-white font-bold">
            <Breadcrumbs
              breadCrumbs={directoryPath}
              mediaTranslations={mediaTranslations}
            />
          </div>
          <div class="p-4">
            <DirectoryContent
              fileIndexState={[fileIndex, setFileIndex]}
              directoryContent={directoryContent}
              mediaTranslations={mediaTranslations}
              selectionMode={selectionMode}
              globalEdit={globalEdit}
            />
          </div>
        </div>
        {fileIndex !== null ? (
          <EditSidebar
            directory={directory}
            fileIndexState={[fileIndex, setFileIndex]}
            directoryContent={directoryContent}
            apiEndpoints={apiEndpoints}
            mediaTranslations={mediaTranslations}
            submitForm={submitForm}
            selectionMode={selectionMode}
            selectMedia={selectMedia}
            onlyImage={onlyImage}
            globalEdit={globalEdit}
            expertMode={expertMode}
            isLoading={isLoading}
          />
        ) : (
          directory && (
            <EditDirectorySidebar
              directory={directory}
              apiEndpoints={apiEndpoints}
              mediaTranslations={mediaTranslations}
              submitForm={submitForm}
              selectionMode={selectionMode}
              globalEdit={globalEdit}
              isLoading={isLoading}
            />
          )
        )}
      </div>
    </div>
  );
}
