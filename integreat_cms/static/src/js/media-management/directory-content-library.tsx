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
        loadingState,
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
    // This callback is used to set the Loading State when doing ajax requests
    const [_isLoading, setLoading] = loadingState;

    // Load the directory path each time the directory id changes
    useEffect(() => {
        const loadDirectory = async () => {
            setLoading(true);
            const urlParams = new URLSearchParams({});
            if (directoryId) {
                console.debug(`Loading directory with id ${directoryId}...`);
                urlParams.append("directory", directoryId);
            } else {
                console.debug(`Loading root directory...`);
            }
            try {
                await Promise.all([
                    directoryId ? ajaxRequest(getDirectoryPath, urlParams, setDirectoryPath) : setDirectoryPath([]),
                    ajaxRequest(getDirectoryContent, urlParams, setMediaLibraryContent),
                ]);
            } finally {
                setLoading(false);
            }

            // Close the file sidebar
            setFileIndex(null);
        };
        loadDirectory();
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
