/*
 * This component renders the media library with applied filters.
 */
import { useEffect } from "preact/hooks";

import Library, { LibraryProps } from "./library";

const FilterResultLibrary = (props: LibraryProps) => {
    const {
        mediaFilter,
        mediaLibraryContentState,
        fileIndexState,
        refreshState,
        ajaxRequest,
        apiEndpoints: { filterUnusedMediaFiles },
    } = props;

    // The directory content contains all subdirectories and files of the current directory
    const [_mediaLibraryContent, setMediaLibraryContent] = mediaLibraryContentState;
    // The file index contains the index of the file which is currently opened in the sidebar
    const [_fileIndex, setFileIndex] = fileIndexState;
    // This state is used to refresh the media library after changes were made
    const [refresh, _setRefresh] = refreshState;

    useEffect(() => {
        if (mediaFilter === "unused") {
            console.debug("Loading unused media files...");
            const urlParams = new URLSearchParams({});
            // Load the filtered result
            ajaxRequest(filterUnusedMediaFiles, urlParams, setMediaLibraryContent);
            // Close the file sidebar
            setFileIndex(null);
        } else {
            console.error("Unsupported filter: ", mediaFilter);
        }
    }, [refresh]); /* eslint-disable-line react-hooks/exhaustive-deps */

    return <Library {...props} />;
};
export default FilterResultLibrary;
