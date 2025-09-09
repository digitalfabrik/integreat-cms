/*
 * Entry point for the media library preact component.
 * Documentation: https://preactjs.com/
 * The directory id is injected from the url via preact-router.
 */

import { render, h } from "preact";
import { useState } from "preact/hooks";
import { Router, route } from "preact-router";
import { createHashHistory } from "history";
import cn from "classnames";

import MessageComponent, { Message } from "./component/message";
import DirectoryContentLibrary from "./directory-content-library";
import SearchResultLibrary from "./search-result-library";
import FilterResultLibrary from "./filter-result-library";

export type MediaApiPaths = {
  getDirectoryPath: string;
  getDirectoryContent: string;
  getSearchResult: string;
  getSearchSuggestions: string;
  getFileUsages: string;
  createDirectory: string;
  editDirectory: string;
  deleteDirectory: string;
  uploadFile: string;
  editFile: string;
  moveFile: string;
  deleteFile: string;
  replaceFile: string;
  filterUnusedMediaFiles: string;
};

export type File = {
  id: number;
  name: string;
  url: string;
  path: string | null;
  altText: string;
  type: string;
  fileSize: string;
  typeDisplay: string;
  thumbnailUrl: string | null;
  uploadedDate: Date;
  lastModified: Date;
  isGlobal: boolean;
  isHidden: boolean;
  deletable: boolean;
};

export type FileUsage = {
  url: string;
  name: string;
  title: string;
};

export type FileUsages = {
  isUsed: boolean;
  iconUsages: FileUsage[] | null;
  contentUsages: FileUsage[] | null;
};

export type Directory = {
  id: number;
  name: string;
  parentId: string;
  numberOfEntries: number;
  CreatedDate: Date;
  isGlobal: boolean;
  isHidden: boolean;
  type: "directory";
};

export type MediaLibraryEntry = Directory | File;

type Props = {
  apiEndpoints: MediaApiPaths;
  mediaTranslations: any;
  onlyImage?: boolean;
  globalEdit?: boolean;
  expertMode?: boolean;
  mediaTypes: { allowedMediaTypes: string };
  selectionMode?: boolean;
  selectMedia?: (file: File) => any;
  canDeleteFile: boolean;
  canReplaceFile: boolean;
  canDeleteDirectory: boolean;
};

const MediaManagement = (props: Props) => {
  const [newMessage, showMessage] = useState<Message | null>(null);
  const [isLoading, setLoading] = useState<boolean>(false);
  const [directoryPath, setDirectoryPath] = useState<Directory[]>([]);
  const [mediaLibraryContent, setMediaLibraryContent] = useState<MediaLibraryEntry[]>([]);
  const [fileIndex, setFileIndex] = useState<number | null>(null);
  const [refresh, setRefresh] = useState<boolean>(false);
  const [sidebarFile, setSidebarFile] = useState<File | null>(null);

  const {
    mediaTranslations: { text_error: textError, text_network_error: textNetworkError },
  } = props;

  const ajaxRequest = async (
    url: string,
    urlParams: URLSearchParams,
    successCallback: (data: any) => void,
    loadingSetter = setLoading
  ) => {
    loadingSetter(true);
    try {
      if (!url) {
        console.warn("ajaxRequest called without URL");
        return;
      }
      const response = await fetch(`${url}?${urlParams}`);
      const HTTP_STATUS_OK = 200;
      if (response.status === HTTP_STATUS_OK) {
        successCallback((await response.json()).data);
      } else {
        console.error("Server error:", response);
        showMessage({ type: "error", text: textError });
        route("/");
      }
    } catch (error) {
      console.error(error);
      showMessage({ type: "error", text: textNetworkError });
    } finally {
      loadingSetter(false);
    }
  };

  // Safe addition of the "use location opening hours" listener
  const addOpeningHoursListener = () => {
    const checkbox = document.getElementById("id_use_location_opening_hours");
    if (checkbox) {
      checkbox.addEventListener("change", () => {
        console.log("Opening hours changed");
      });
    }
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
        <FilterResultLibrary
          path="/filter/:mediaFilter+/"
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
};

export default MediaManagement;

// Safe DOMContentLoaded initialization
document.addEventListener("DOMContentLoaded", () => {
  document.querySelectorAll("integreat-media-management").forEach((el) => {
    const mediaConfigElement = document.getElementById("media_config_data");
    if (!mediaConfigElement) return;

    const mediaConfigData = JSON.parse(mediaConfigElement.textContent || "{}");
    render(
      <MediaManagement
        {...mediaConfigData}
        globalEdit={el.hasAttribute("data-enable-global-edit")}
      />,
      el
    );
  });

  document.querySelectorAll("a:not([media-library-link])").forEach((link) => {
    link.setAttribute("native", "");
  });

  // Add the opening hours listener safely
  const checkbox = document.getElementById("id_use_location_opening_hours");
  if (checkbox) {
    checkbox.addEventListener("change", () => {
      console.log("Opening hours changed");
    });
  }
});

(window as any).IntegreatMediaManagement = MediaManagement;
(window as any).preactRender = render;
(window as any).preactJSX = h;