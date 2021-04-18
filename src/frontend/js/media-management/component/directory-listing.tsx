import { Link } from "preact-router";
import { useEffect, useState } from "preact/hooks";
import { MediaApiPaths } from "..";
import DirectoryEntry from "./directory-entry";
import FileEntry from "./file-entry";

interface Props {
  parentDirectory: number | null;
  apiEndpoints: MediaApiPaths;
  refresh: number;
  setEditFile: (file: File) => void;
}

export interface File {
  isGlobal: boolean;
  id: number;
  name: string;
  path: string;
  alt_text: string;
  file_type: string;
  thumbnailPath?: string;
  uploadedAt: Date;
  type: "file";
}

export interface Directory {
  isGlobal: any;
  id: number;
  name: string;
  numberOfEntries: number;
  type: "directory";
}

type MediaLibraryEntry = File | Directory;

export default function DirectoryListing({
  parentDirectory,
  apiEndpoints,
  setEditFile,
  refresh,
}: Props) {
  const [error, setError] = useState(null);
  const [isLoaded, setIsLoaded] = useState(false);
  const [items, setItems] = useState<MediaLibraryEntry[]>([]);

  useEffect(() => {
    (async () => {
      setItems([]);
      setIsLoaded(false);
      try {
        let url = apiEndpoints.getDirectoryContent;
        if (parentDirectory) {
          url += "?directory=" + parentDirectory;
        }
        const result = await fetch(url);
        const data = await result.json();
        if (!data.success) {
          setError(true);
        }
        setItems(data.data);
      } catch (e) {
        console.error(e);
        setError(true);
      }
      setIsLoaded(true);
    })();
  }, [parentDirectory, refresh]);

  return (
    <div className="grid grid-cols-gallery max-h-full overflow-y-auto">
      {items.map((item) =>
        item.type === "directory" ? (
          <Link href={`/listing/${item.id}`}>
            <DirectoryEntry item={item} />
          </Link>
        ) : (
          <FileEntry
            item={item}
            onClick={(e) => {
              e.stopPropagation();
              setEditFile(item);
            }}
          />
        )
      )}
    </div>
  );
}
