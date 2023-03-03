/*
 * This component renders a grid of all subdirectories and all files of the current directory
 */
import { Link } from "preact-router";
import { StateUpdater } from "preact/hooks";

import { MediaLibraryEntry, File, Directory } from "..";
import DirectoryEntry from "./directory-entry";
import FileEntry from "./file-entry";

export type DraggedElement = {
    type: "file" | "directory";
    id: number;
};

type Props = {
    fileIndexState: [number | null, StateUpdater<number | null>];
    mediaLibraryContent: MediaLibraryEntry[];
    mediaTranslations: any;
    globalEdit?: boolean;
    allowDrop: boolean;
    setDraggedItem: (item: DraggedElement) => unknown;
    dropItem: (directoryId: number) => unknown;
};

const DirectoryContent = ({
    fileIndexState,
    mediaLibraryContent,
    mediaTranslations,
    globalEdit,
    setDraggedItem,
    dropItem,
    allowDrop,
}: Props) => {
    // The file index contains the index of the file which is currently opened in the sidebar
    const [fileIndex, setFileIndex] = fileIndexState;
    return (
        <div className="grid grid-cols-gallery max-h-full gap-1">
            {mediaLibraryContent.map((entry: MediaLibraryEntry, index: number) =>
                entry.type === "directory" ? (
                    <Link key={`dir-${entry.id}`} href={`/${entry.id}/`} media-library-link>
                        <DirectoryEntry
                            directory={entry as Directory}
                            mediaTranslations={mediaTranslations}
                            globalEdit={globalEdit}
                            allowDrop={(!(entry as Directory).isGlobal || globalEdit) && allowDrop}
                            itemDropped={() => dropItem(entry.id)}
                            dragStart={() => setDraggedItem({ type: "directory", id: entry.id })}
                            dragEnd={() => setDraggedItem(null)}
                        />
                    </Link>
                ) : (
                    <FileEntry
                        key={`file-${entry.id}`}
                        file={entry as File}
                        active={index === fileIndex}
                        onClick={(e) => {
                            e.stopPropagation();
                            setFileIndex(index);
                        }}
                        mediaTranslations={mediaTranslations}
                        globalEdit={globalEdit}
                        dragStart={() => setDraggedItem({ type: "file", id: entry.id })}
                        dragEnd={() => setDraggedItem(null)}
                    />
                )
            )}
        </div>
    );
};
export default DirectoryContent;
