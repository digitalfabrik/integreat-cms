/*
 * This component renders the media library in when a directory is viewed.
 */
import { useEffect } from "preact/hooks";

import Library, { LibraryProps } from "./library";

const DirectoryContentLibrary = (props: LibraryProps) => {
    const {
        directoryPathState,
        mediaLibraryContentState,
        fileIndexState,
        refreshState,
        directoryId,
        ajaxRequest,
        apiEndpoints: { getDirectoryContent, getDirectoryPath },
    } = props;
    // The directory path contains the current directory and all its parents
    const [directoryPath, setDirectoryPath] = directoryPathState;
    // The current directory is the last element of the directory path
    const directory = directoryPath[directoryPath.length - 1];
    // The directory content contains all subdirectories and files of the current directory
    const [_mediaLibraryContent, setMediaLibraryContent] = mediaLibraryContentState;
    // The file index contains the index of the file which is currently opened in the sidebar
    const [_fileIndex, setFileIndex] = fileIndexState;
    // This state is used to refresh the media library after changes were made
    const [refresh, _setRefresh] = refreshState;

    // Load the directory path each time the directory id changes
    useEffect(() => {
        // Reset search query buffer
        const urlParams = new URLSearchParams({});
        if (directoryId) {
            console.debug(`Loading directory with id ${directoryId}...`);
            urlParams.append("directory", directoryId);
        } else {
            console.debug(`Loading root directory...`);
        }
        // Load the new directory path
        if (directoryId) {
            ajaxRequest(getDirectoryPath, urlParams, setDirectoryPath);
        } else {
            // The root directory is no real directory object, so the path is empty
            setDirectoryPath([]);
        }
        // Load the new directory content
        ajaxRequest(getDirectoryContent, urlParams, setMediaLibraryContent);

        // Close the file sidebar
        setFileIndex(null);
        /* eslint-disable-next-line react-hooks/exhaustive-deps */
    }, [directoryId, refresh]);

    // Debug output on directory change
    useEffect(() => {
        if (directory) {
            console.debug(`Changed to directory with id ${directoryId}:`, directory);
        } else if (!directoryId) {
            console.debug("Changed to root directory");
        }
        /* eslint-disable-next-line react-hooks/exhaustive-deps */
    }, [directory]);

    return <Library {...props} />;
};
export default DirectoryContentLibrary;
