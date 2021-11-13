/*
 * This component renders a selection dialog to select a specific file from the media library.
 * On selection, the given selection handler selectMedia() is executed.
 */
import { XCircle } from "preact-feather";

import MediaManagement, { File, MediaApiPaths } from ".";

interface Props {
  cancel: () => any;
  onlyImage: boolean;
  selectMedia: (file: File) => any;
  apiEndpoints: MediaApiPaths;
  mediaTranslations: any;
}

export default function SelectMedia({
  cancel,
  onlyImage,
  selectMedia,
  apiEndpoints,
  mediaTranslations,
}: Props) {
  return (
    <div
      className="flex flex-col items-center justify-center w-full h-full fixed inset-0 z-50 m-auto"
      style="z-index: 2000;"
    >
      <div className="w-10/12 h-5/6 flex flex-col justify-center relative">
        <div class="flex w-full h-full content bg-gray-200 p-4 shadow-md rounded overflow-auto">
          <MediaManagement
            selectionMode
            onlyImage={onlyImage}
            selectMedia={selectMedia}
            apiEndpoints={apiEndpoints}
            mediaTranslations={mediaTranslations}
          ></MediaManagement>
        </div>
        <button onClick={cancel} className="hover:text-blue-500 absolute top-6 right-3">
          <XCircle className="inline-block h-8 w-8" />
        </button>
      </div>
    </div>
  );
}

(window as any).IntegreatSelectMediaDialog = SelectMedia;
