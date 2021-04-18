import { render } from "preact";
import { Search } from "preact-feather";
import { useEffect, useState } from "preact/hooks";
import { MediaApiPaths } from ".";
import MediacenterBreadcrumb from "./component/breadcrumb";
import Button from "./component/button";
import DirectoryListing, {
  Directory,
  File,
} from "./component/directory-listing";
import EditSidebar from "./component/edit-sidebar";

interface Props {
  apiEndpoints: MediaApiPaths;
  mediaTranslations: any;
  parentDirectory?: number | null;
  path?: string;
  default?: true;
  selectionMode?: boolean;
  selectMedia?: (file: File) => any;
  globalEdit?: boolean;
}

export default function Listing(props: Props) {
  const [editFile, setEditFile] = useState<File | null>(null);
  const [refreshCounter, setRefreshCounter] = useState(0);

  const [directory, setDirectory] = useState<Directory | null>(null);

  useEffect(() => {
    if (props.parentDirectory) {
      (async () => {
        try {
          let url = props.apiEndpoints.getDirectoryPath;
          url += "?directory=" + props.parentDirectory;

          const result = await fetch(url);
          const data = await result.json();

          setDirectory(data.data[data.data.length - 1]);
        } catch (e) {
          console.error(e);
        }
      })();
    } else {
      setDirectory(null);
    }
  }, [props.parentDirectory]);

  return (
    <div className="max-h-full flex flex-col w-full">
      <div className="flex flex-wrap items-center">
        <h1 className="w-full heading p-2">
          {props.mediaTranslations.label_media_library}
        </h1>
        <form class="table-search relative w-1/2">
            <Search class="absolute m-2" />
            <input type="search" class="h-full py-2 pl-10 pr-4 rounded shadow" />
        </form>
        <div className="flex-1"></div>
        {!props.selectionMode && (props.globalEdit || !directory?.isGlobal) && (
          <div className="flex flex-wrap justify-start">
            <Button
              href={`/create_directory/${props.parentDirectory || 0}`}
              label={props.mediaTranslations.btn_create_directory}
            />
            <Button
              href={`/upload_file/${props.parentDirectory || 0}`}
              label={props.mediaTranslations.btn_upload_file}
            />
          </div>
        )}
      </div>
      <MediacenterBreadcrumb
        directoryId={props.parentDirectory}
        apiEndpoints={props.apiEndpoints}
        mediaTranslations={props.mediaTranslations}
      />
      <div className="flex flex-1 overflow-auto items-stretch bg-white border-gray-800 shadow-sm rounded min-h-screen">
        <div className="flex-1 pt-5" onClick={() => setEditFile(null)}>
          <DirectoryListing
            parentDirectory={props.parentDirectory}
            apiEndpoints={props.apiEndpoints}
            setEditFile={setEditFile}
            refresh={refreshCounter}
          ></DirectoryListing>
        </div>
        {editFile && (
          <EditSidebar
            file={editFile}
            mediaTranslations={props.mediaTranslations}
            editMediaEndpoint={props.apiEndpoints.editMediaUrl}
            deleteMediaEndpoint={props.apiEndpoints.deleteMediaUrl}
            finishEditSidebar={() => {
              setEditFile(null);
              setRefreshCounter(refreshCounter + 1);
            }}
            selectionMode={props.selectionMode}
            selectMedia={props.selectMedia}
            globalEdit={props.globalEdit}
          ></EditSidebar>
        )}
      </div>
    </div>
  );
}
