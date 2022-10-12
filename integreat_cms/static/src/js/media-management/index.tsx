/*
 * This file contains the entrypoint for the media library preact component.
 *
 * Documentation of preact: https://preactjs.com/
 *
 * The directory id is injected from the url into the preact component via preact router:
 * https://github.com/preactjs/preact-router
 */
import { render, h } from "preact";
import { useState } from "preact/hooks";
import { Router, route } from 'preact-router';
import { createHashHistory } from "history";
import cn from "classnames";

import MessageComponent, { Message } from "./component/message";
import DirectoryContentLibrary from "./directory-content-library";
import SearchResultLibrary from "./search-result-library";

export interface MediaApiPaths {
  getDirectoryPath: string;
  getDirectoryContent: string;
  getSearchResult:string;
  getSearchSuggestions:string;
  createDirectory: string;
  editDirectory: string;
  deleteDirectory: string;
  uploadFile: string;
  editFile: string;
  moveFile: string;
  deleteFile: string;
  replaceFile: string;
}

export interface File {
  id: number;
  name: string;
  url: string | null;
  path: string | null;
  altText: string;
  type: string;
  fileSize: string;
  typeDisplay: string;
  thumbnailUrl: string | null;
  uploadedDate: Date;
  lastModified: Date;
  isGlobal: boolean;
}

export interface Directory {
  id: number;
  name: string;
  parentId: string;
  numberOfEntries: number;
  CreatedDate: Date;
  isGlobal: boolean;
  type: "directory";
}

export type MediaLibraryEntry = Directory | File;

interface Props {
  apiEndpoints: MediaApiPaths;
  mediaTranslations: any;
  onlyImage?: boolean;
  globalEdit?: boolean;
  expertMode?: boolean;
  allowedMediaTypes?: string;
  selectionMode?: boolean;
  selectMedia?: (file: File) => any;
}

export default function MediaManagement(props: Props) {
  // This state can be used to show a success or error message
  const [newMessage, showMessage] = useState<Message | null>(null);
  // This state is a semaphore to block actions while an ajax call is running
  const [isLoading, setLoading] = useState<boolean>(false);
  // The directory path contains the current directory and all its parents
  const [directoryPath, setDirectoryPath] = useState<Directory[]>([]);
  // The directory content contains all subdirectories and files of the current directory
  const [mediaLibraryContent, setMediaLibraryContent] = useState<MediaLibraryEntry[]>([]);
  // The file index contains the index of the file which is currently opened in the sidebar
  const [fileIndex, setFileIndex] = useState<number | null>(null);
  // This state is used to refresh the media library after changes were made
  const [refresh, setRefresh] = useState<boolean>(false);
  // This state contains a file which should be opened in the sidebar after the content has been refreshed
  const [sidebarFile, setSidebarFile] = useState<File>(null);

  // This function is used to get information about a directory (either the path or the content)
  const ajaxRequest = async (
      url: string,
      urlParams: URLSearchParams,
      successCallback: (data: any) => void
  ) => {
    setLoading(true);
    try {
      const response = await fetch(
          `${url}?${urlParams}`
      );
      if (response.status === 200) {
        successCallback((await response.json()).data);
      } else {
        console.error("Server error:", response);
        showMessage({
          type: "error",
          text: props.mediaTranslations.text_error,
        });
        route("/");
      }
    } catch (error) {
      console.error(error);
      showMessage({
        type: "error",
        text: props.mediaTranslations.text_network_error,
      });
    }
    setLoading(false);
  };

  return (
    <div className={cn("flex flex-col flex-grow min-w-0", { "cursor-wait": isLoading })}>
      <MessageComponent newMessage={newMessage} />
      <Router history={createHashHistory() as any}>
        <SearchResultLibrary
            path="/search/:searchQuery+"
            showMessage={showMessage}
            loadingState={[isLoading, setLoading]}
            refreshState={[refresh, setRefresh]}
            directoryPathState={[directoryPath, setDirectoryPath]}
            mediaLibraryContentState={[mediaLibraryContent, setMediaLibraryContent]}
            fileIndexState={[fileIndex, setFileIndex]}
            sidebarFileState={[sidebarFile, setSidebarFile]}
            ajaxRequest={ajaxRequest}
            {...props}
        />
        <DirectoryContentLibrary
            path="/:directoryId?"
            showMessage={showMessage}
            loadingState={[isLoading, setLoading]}
            refreshState={[refresh, setRefresh]}
            directoryPathState={[directoryPath, setDirectoryPath]}
            mediaLibraryContentState={[mediaLibraryContent, setMediaLibraryContent]}
            fileIndexState={[fileIndex, setFileIndex]}
            sidebarFileState={[sidebarFile, setSidebarFile]}
            ajaxRequest={ajaxRequest}
            {...props}
        />
      </Router>
    </div>
  );
}

document.addEventListener("DOMContentLoaded", () => {
  document.querySelectorAll("integreat-media-management").forEach((el) => {
    const mediaConfigData = JSON.parse(document.getElementById("media_config_data").textContent);
    render(
      <MediaManagement
        {...mediaConfigData}
        globalEdit={el.hasAttribute("data-enable-global-edit")}
      />,
      el
    );
  });
  // mark all non-media-library-links as "native" so they are routed by the browser instead of preact
  document.querySelectorAll("a:not([media-library-link])").forEach((link) => {
    link.setAttribute("native", "");
  });
});

(window as any).IntegreatMediaManagement = MediaManagement;
(window as any).preactRender = render;
(window as any).preactJSX = h;
