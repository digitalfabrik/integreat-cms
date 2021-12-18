/*
 * This component renders the media library with search results.
 */
import { useEffect } from "preact/hooks";

import Library, {LibraryProps} from "./library";

export default function SearchResultLibrary(props: LibraryProps) {

  // The directory content contains all subdirectories and files of the current directory
  const [mediaLibraryContent, setMediaLibraryContent] = props.mediaLibraryContentState;
  // The file index contains the index of the file which is currently opened in the sidebar
  const [fileIndex, setFileIndex] = props.fileIndexState;
  // This state is used to refresh the media library after changes were made
  const [refresh, setRefresh] = props.refreshState;

  useEffect(() => {
    const urlParams = new URLSearchParams({
      query: props.searchQuery
    })
    console.debug(`Loading search result for query "${props.searchQuery}"...`);
    // Load the search result
    props.ajaxRequest(
        props.apiEndpoints.getSearchResult,
        urlParams,
        setMediaLibraryContent
    );
    // Close the file sidebar
    setFileIndex(null);
  }, [props.searchQuery, refresh])

  return (
      <Library
          {...props}
      />
  );
}
