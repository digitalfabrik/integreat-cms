/*
 * This component renders a grid of all subdirectories and all files of the current directory
 */
import { Link } from "preact-router";
import { StateUpdater } from "preact/hooks";

import { MediaLibraryEntry, File, Directory } from "..";
import DirectoryEntry from "./directory-entry";
import FileEntry from "./file-entry";

interface Props {
  fileIndexState: [number | null, StateUpdater<number | null>];
  directoryContent: MediaLibraryEntry[];
  mediaTranslations: any;
  globalEdit?: boolean;
}

export default function DirectoryContent({
  fileIndexState,
  directoryContent,
  mediaTranslations,
  globalEdit,
}: Props) {
  // The file index contains the index of the file which is currently opened in the sidebar
  const [fileIndex, setFileIndex] = fileIndexState;

  return (
    <div className="grid grid-cols-gallery max-h-full gap-1">
      {directoryContent.map((entry: MediaLibraryEntry, index: number) =>
        entry.type === "directory" ? (
          <Link href={`/${entry.id}/`} media-library-link>
            <DirectoryEntry
              directory={entry as Directory}
              mediaTranslations={mediaTranslations}
              globalEdit={globalEdit}
            />
          </Link>
        ) : (
          <FileEntry
            file={entry as File}
            active={index === fileIndex}
            onClick={(e) => {
              e.stopPropagation();
              setFileIndex(index);
            }}
            mediaTranslations={mediaTranslations}
            globalEdit={globalEdit}
          />
        )
      )}
    </div>
  );
}
