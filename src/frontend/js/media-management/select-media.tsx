import { render } from "preact";
import { XCircle } from "preact-feather";
import MediaManagement, { MediaApiPaths } from ".";
import { File } from "./component/directory-listing";

interface Props {
  cancel: () => any;
  selectMedia: (file: File) => any;
  apiEndpoints: MediaApiPaths;
  mediaTranslations: any;
}

export default function SelectMedia({
  cancel,
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
        <div class="h-full content bg-gray-200 w-full p-4 shadow-md rounded">
          <MediaManagement
            selectionMode
            selectMedia={selectMedia}
            apiEndpoints={apiEndpoints}
            mediaTranslations={mediaTranslations}
          ></MediaManagement>
        </div>
        <button onClick={cancel} className="absolute top-6 right-3">
          <XCircle className="inline-block h-8 w-8" />
        </button>
      </div>
    </div>
  );
}

(window as any).IntegreatSelectMediaDialog = SelectMedia;
