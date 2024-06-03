/*
 * This component renders the media library in edit mode,
 * so new directories and files can be added and the existing entries can be modified
 */
import { FilePlus, FolderPlus, Search, Loader, Filter, FilterX, X } from "lucide-preact";
import { StateUpdater, useEffect, useState } from "preact/hooks";
import { route } from "preact-router";
import cn from "classnames";

import { Directory, MediaApiPaths, MediaLibraryEntry, File } from ".";
import Breadcrumbs from "./component/breadcrumbs";
import DirectoryContent, { DraggedElement } from "./component/directory-content";
import EditDirectorySidebar from "./component/edit-directory-sidebar";
import EditSidebar from "./component/edit-sidebar";
import { Message } from "./component/message";
import CreateDirectory from "./component/create-directory";
import UploadFile from "./component/upload-file";
import { setSearchQueryEventListeners } from "../search-query";
import { getCsrfToken } from "../utils/csrf-token";

export type LibraryProps = {
    /* eslint-disable-next-line react/no-unused-prop-types */
    path?: string;
    directoryId?: string;
    searchQuery?: string;
    mediaFilter?: string;
    loadingState: [boolean, StateUpdater<boolean>];
    refreshState: [boolean, StateUpdater<boolean>];
    mediaLibraryContentState: [MediaLibraryEntry[], StateUpdater<MediaLibraryEntry[]>];
    directoryPathState: [Directory[], StateUpdater<Directory[]>];
    fileIndexState: [number, StateUpdater<number>];
    sidebarFileState: [File, StateUpdater<File>];
    showMessage: StateUpdater<Message>;
    apiEndpoints: MediaApiPaths;
    mediaTranslations: any;
    globalEdit?: boolean;
    expertMode?: boolean;
    mediaTypes: { allowedMediaTypes: string };
    selectionMode?: boolean;
    onlyImage?: boolean;
    selectMedia?: (file: File) => any;
    ajaxRequest: (
        url: string,
        urlParams: URLSearchParams,
        successCallback: (data: any) => void,
        loadingSetter?: StateUpdater<boolean>
    ) => void;
    canDeleteFile: boolean;
    canReplaceFile: boolean;
    canDeleteDirectory: boolean;
};

const Library = ({
    directoryId,
    searchQuery,
    mediaFilter,
    loadingState,
    refreshState,
    mediaLibraryContentState,
    directoryPathState,
    fileIndexState,
    sidebarFileState,
    apiEndpoints,
    mediaTranslations,
    mediaTypes,
    globalEdit,
    expertMode,
    selectionMode,
    onlyImage,
    showMessage,
    selectMedia,
    canDeleteFile,
    canReplaceFile,
    canDeleteDirectory,
    ajaxRequest,
}: LibraryProps) => {
    // The directory path contains the current directory and all its parents
    const [directoryPath, setDirectoryPath] = directoryPathState;
    // The current directory is the last element of the directory path
    const directory = directoryPath[directoryPath.length - 1];
    // The directory content contains all subdirectories and files of the current directory
    const [mediaLibraryContent, _setMediaLibraryContent] = mediaLibraryContentState;
    // The file index contains the index of the file which is currently opened in the sidebar
    const [fileIndex, setFileIndex] = fileIndexState;
    // This state is a semaphore to block actions while an ajax call is running
    const [isLoading, setLoading] = loadingState;
    // This state contains a file which should be opened in the sidebar after the content has been refreshed
    const [sidebarFile, setSidebarFile] = sidebarFileState;
    // This state is used to refresh the media library after changes were made
    const [refresh, setRefresh] = refreshState;
    // Whether or not the create directory form should be shown
    const [isCreateDirectory, setCreateDirectory] = useState<boolean>(false);
    // Whether or not the file upload form should be shown
    const [isUploadFile, setUploadFile] = useState<boolean>(false);

    const [draggedItem, setDraggedItem] = useState<DraggedElement | null>(null);

    const moveIntoDirectory = async (targetDirectoryId: number) => {
        (document.getElementById("parent_directory") as HTMLInputElement).value =
            targetDirectoryId === 0 ? "" : targetDirectoryId.toString();
        (document.getElementById("media-move-btn") as HTMLInputElement).click();
    };

    const HTTP_STATUS_OK = 200;

    // This submit function is used for all form submissions
    const submitForm = async (event: Event, successCallback?: (data: any) => void) => {
        event.preventDefault();
        setLoading(true);
        console.debug("Submitting form:", event.target);
        const form = event.target as HTMLFormElement;

        try {
            const response = await fetch(form.action, {
                method: "POST",
                headers: {
                    "X-CSRFToken": getCsrfToken(),
                },
                body: new FormData(form),
            });
            console.debug(response);
            const data = await response.json();
            console.debug(data);
            if (response.status === HTTP_STATUS_OK) {
                console.debug("Form submission successful!");
                if (typeof successCallback === "function") {
                    console.debug("Calling success callback...");
                    successCallback(data);
                }
                console.debug("Refreshing media library...");
                setRefresh(!refresh);
                if (data.file) {
                    setSidebarFile(data.file);
                }
            }
            if (data.messages) {
                data.messages.forEach(showMessage);
            } else if (response.status !== HTTP_STATUS_OK) {
                showMessage({
                    type: "error",
                    text: mediaTranslations.text_error,
                });
            }
        } catch (error) {
            console.error("Submitting Form failed:", error);
            showMessage({
                type: "error",
                text: mediaTranslations.text_network_error,
            });
        }
        setLoading(false);
    };

    // Open the file in the sidebar after a refresh
    useEffect(() => {
        // Search for the sidebar file in the media library content
        if (sidebarFile) {
            console.debug("Changed file:", sidebarFile);
            const index = mediaLibraryContent.findIndex((x) => x.id === sidebarFile.id && x.type !== "directory");
            if (index !== -1) {
                console.debug(`Open changed file at index ${index} in the sidebar again after reload...`);
                // Open file in the sidebar
                setFileIndex(index);
                // Reset sidebar buffer
                setSidebarFile(null);
            } else {
                console.debug(`Changed file not found, close sidebar...`);
                // Reset buffer
                setFileIndex(null);
                setSidebarFile(null);
            }
        }
        /* eslint-disable-next-line react-hooks/exhaustive-deps */
    }, [mediaLibraryContent]);

    // Set the search query event listeners after a refresh
    useEffect(setSearchQueryEventListeners, [mediaLibraryContent]);

    return (
        <div className="flex flex-col flex-grow h-full overflow-hidden">
            <h1 className="w-full heading p-2">{mediaTranslations.heading_media_library}</h1>
            <div className="flex flex-wrap justify-between gap-x-2 gap-y-4">
                <div className="flex flex-wrap justify-start gap-2">
                    <div id="table-search" class="flex">
                        <form
                            id="media-move-form"
                            class="hidden"
                            method="POST"
                            encType="multipart/form-data"
                            onSubmit={submitForm}
                            action={apiEndpoints.moveFile}>
                            <input name="mediafile_id" value={draggedItem?.id} />
                            <input name="parent_directory" id="parent_directory" />
                            <input id="media-move-btn" type="submit" />
                        </form>
                        <form
                            id="media-search-form"
                            class="relative"
                            onSubmit={(event) => {
                                event.preventDefault();
                                const searchInput = document.getElementById("table-search-input") as HTMLInputElement;
                                console.debug(`Search form submitted with query "${searchInput.value}"...`);
                                if (!searchInput.value) {
                                    console.debug(`Search query empty, returning to the home directory...`);
                                    route("/");
                                } else {
                                    // Clear focus
                                    if (document.activeElement instanceof HTMLElement) {
                                        document.activeElement.blur();
                                    }
                                    setDirectoryPath([]);
                                    route(`/search/${encodeURIComponent(searchInput.value)}`);
                                }
                            }}>
                            <input
                                id="table-search-input"
                                form="media-search-form"
                                type="search"
                                autocomplete="off"
                                placeholder={mediaTranslations.btn_search}
                                className={cn("rounded-r-none", {
                                    "!bg-gray-100 !border-gray-100": selectionMode,
                                })}
                                data-url={apiEndpoints.getSearchSuggestions}
                                data-object-type="media"
                                data-archived="false"
                                value={searchQuery}
                            />
                            <div
                                id="table-search-suggestions"
                                class="absolute hidden shadow rounded-b top-full bg-graz-200 w-full z-10 max-h-60 overflow-y-auto cursor-pointer"
                            />
                        </form>
                        {searchQuery && (
                            <button
                                id="search-reset-btn"
                                title={mediaTranslations.btn_reset_search}
                                className={cn("hover:bg-gray-300 text-gray-800 py-2 px-3", {
                                    "bg-gray-100 border-gray-100": selectionMode,
                                    "bg-gray-200 border-gray-200": !selectionMode,
                                })}
                                type="button"
                                aria-label="Reset">
                                <X className="w-5" />
                            </button>
                        )}
                        <button
                            id="search-submit-btn"
                            title={mediaTranslations.btn_search}
                            class="bg-blue-500 hover:bg-blue-600 text-white rounded-r py-2 px-3"
                            type="submit"
                            form="media-search-form"
                            aria-label="Search">
                            <Search className="w-5" />
                        </button>
                    </div>
                    <div>
                        {mediaFilter ? (
                            <button
                                id="show-all-files-btn"
                                title={mediaTranslations.btn_reset_filter}
                                className="btn btn-ghost"
                                type="submit"
                                onClick={() => route("/")}>
                                <FilterX className="inline-block mr-2 h-5" />
                                {mediaTranslations.btn_reset_filter}
                            </button>
                        ) : (
                            <button
                                id="unused-media-filter-btn"
                                title={mediaTranslations.btn_filter_unused}
                                className="btn btn-ghost"
                                type="submit"
                                action={apiEndpoints.filterUnusedMediaFiles}
                                onClick={() => {
                                    setDirectoryPath([]);
                                    route("/filter/unused/");
                                }}>
                                <Filter className="inline-block mr-2 h-5" />
                                {mediaTranslations.btn_filter_unused}
                            </button>
                        )}
                    </div>
                </div>
                {(globalEdit || !directory?.isGlobal) && !searchQuery && !mediaFilter && (
                    <div className="flex flex-wrap justify-start gap-2">
                        <button
                            title={mediaTranslations.btn_create_directory}
                            class="btn"
                            type="submit"
                            onClick={() => setCreateDirectory(!isCreateDirectory)}>
                            <FolderPlus class="inline-block mr-2 h-5" />
                            {mediaTranslations.btn_create_directory}
                        </button>
                        <button
                            title={mediaTranslations.btn_upload_file}
                            class="btn"
                            type="submit"
                            onClick={() => setUploadFile(!isUploadFile)}>
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
                            mediaTypes={mediaTypes}
                            submitForm={submitForm}
                            setUploadFile={setUploadFile}
                            isLoading={isLoading}
                            refreshState={[refresh, setRefresh]}
                        />
                    )}
                </div>
            )}
            <div className="flex flex-1 relative flex-row gap-4 mt-4">
                <div className="relative flex-1">
                    <div
                        className="absolute w-full h-full flex flex-col bg-white border border-blue-500 shadow-2xl rounded"
                        onClick={() => setFileIndex(null)}
                        onKeyDown={() => setFileIndex(null)}>
                        <div class="rounded w-full bg-water-500 font-bold">
                            <Breadcrumbs
                                breadCrumbs={directoryPath}
                                searchQuery={searchQuery}
                                mediaTranslations={mediaTranslations}
                                allowDrop={draggedItem !== null}
                                dropItem={moveIntoDirectory}
                                mediaFilter={mediaFilter}
                            />
                        </div>
                        {isLoading ? (
                            <Loader class="absolute w-32 h-32 -mt-9 -ml-16 inset-1/2 text-gray-600 animate-spin" />
                        ) : (
                            <div class="flex-1 p-4 overflow-auto">
                                <DirectoryContent
                                    fileIndexState={[fileIndex, setFileIndex]}
                                    mediaLibraryContent={mediaLibraryContent}
                                    mediaTranslations={mediaTranslations}
                                    globalEdit={globalEdit}
                                    allowDrop={draggedItem !== null}
                                    setDraggedItem={setDraggedItem}
                                    dropItem={moveIntoDirectory}
                                />
                            </div>
                        )}
                    </div>
                </div>

                {fileIndex !== null ? (
                    <div className="relative w-56 md:w-72 lg:w-96 2xl:w-120">
                        <EditSidebar
                            fileIndexState={[fileIndex, setFileIndex]}
                            mediaLibraryContent={mediaLibraryContent}
                            apiEndpoints={apiEndpoints}
                            mediaTranslations={mediaTranslations}
                            submitForm={submitForm}
                            ajaxRequest={ajaxRequest}
                            selectionMode={selectionMode}
                            selectMedia={selectMedia}
                            onlyImage={onlyImage}
                            globalEdit={globalEdit}
                            expertMode={expertMode}
                            isLoading={isLoading}
                            canDeleteFile={canDeleteFile}
                            canReplaceFile={canReplaceFile}
                        />
                    </div>
                ) : (
                    directory && (
                        <div className="relative w-56 md:w-72 lg:w-96 2xl:w-120">
                            <EditDirectorySidebar
                                directory={directory}
                                apiEndpoints={apiEndpoints}
                                mediaTranslations={mediaTranslations}
                                submitForm={submitForm}
                                globalEdit={globalEdit}
                                isLoading={isLoading}
                                canDeleteDirectory={canDeleteDirectory}
                            />
                        </div>
                    )
                )}
            </div>
        </div>
    );
};
export default Library;
