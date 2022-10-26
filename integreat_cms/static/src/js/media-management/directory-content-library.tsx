/*
 * This component renders the media library in when a directory is viewed.
 */
import { useEffect } from "preact/hooks";

import Library, { LibraryProps } from "./library";

export default function DirectoryContentLibrary(props: LibraryProps) {
    // The directory path contains the current directory and all its parents
    const [directoryPath, setDirectoryPath] = props.directoryPathState;
    // The current directory is the last element of the directory path
    const directory = directoryPath[directoryPath.length - 1];
    // The directory content contains all subdirectories and files of the current directory
    const [mediaLibraryContent, setMediaLibraryContent] = props.mediaLibraryContentState;
    // The file index contains the index of the file which is currently opened in the sidebar
    const [fileIndex, setFileIndex] = props.fileIndexState;
    // This state is used to refresh the media library after changes were made
    const [refresh, setRefresh] = props.refreshState;

    // Load the directory path each time the directory id changes
    useEffect(() => {
        // Reset search query buffer
        let urlParams = new URLSearchParams({});
        if (props.directoryId) {
            console.debug(`Loading directory with id ${props.directoryId}...`);
            urlParams.append("directory", props.directoryId);
        } else {
            console.debug(`Loading root directory...`);
        }
        // Load the new directory path
        if (props.directoryId) {
            props.ajaxRequest(props.apiEndpoints.getDirectoryPath, urlParams, setDirectoryPath);
        } else {
            // The root directory is no real directory object, so the path is empty
            setDirectoryPath([]);
        }
        // Load the new directory content
        props.ajaxRequest(props.apiEndpoints.getDirectoryContent, urlParams, setMediaLibraryContent);
        // Close the file sidebar
        setFileIndex(null);
    }, [props.directoryId, refresh]);

    // Debug output on directory change
    useEffect(() => {
        if (directory) {
            console.debug(`Changed to directory with id ${props.directoryId}:`, directory);
        } else if (!props.directoryId) {
            console.debug("Changed to root directory");
        }
    }, [directory]);

    return <Library {...props} />;
}
