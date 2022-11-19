/*
 * This component renders the media library with search results.
 */
import { useEffect } from "preact/hooks";

import Library, { LibraryProps } from "./library";

const SearchResultLibrary = (props: LibraryProps) => {
    const {
        mediaLibraryContentState,
        fileIndexState,
        refreshState,
        searchQuery,
        ajaxRequest,
        apiEndpoints: { getSearchResult },
    } = props;

    // The directory content contains all subdirectories and files of the current directory
    const [_mediaLibraryContent, setMediaLibraryContent] = mediaLibraryContentState;
    // The file index contains the index of the file which is currently opened in the sidebar
    const [_fileIndex, setFileIndex] = fileIndexState;
    // This state is used to refresh the media library after changes were made
    const [refresh, _setRefresh] = refreshState;

    useEffect(() => {
        const urlParams = new URLSearchParams({
            query: searchQuery,
        });
        console.debug(`Loading search result for query "${searchQuery}"...`);
        // Load the search result
        ajaxRequest(getSearchResult, urlParams, setMediaLibraryContent);
        // Close the file sidebar
        setFileIndex(null);
        /* eslint-disable-next-line react-hooks/exhaustive-deps */
    }, [searchQuery, refresh]);

    return <Library {...props} />;
};
export default SearchResultLibrary;
