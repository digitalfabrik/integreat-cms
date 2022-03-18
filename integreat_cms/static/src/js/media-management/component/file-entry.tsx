/*
 * This component renders a file entry within the current directory
 */
import { FileText, Image, Lock } from "preact-feather";
import cn from "classnames";

import { File } from "..";

interface Props {
  file: File;
  active: boolean;
  onClick: (event: MouseEvent) => void;
  mediaTranslations: any;
  globalEdit?: boolean;
}

export default function FileEntry({ file, active, onClick, mediaTranslations, globalEdit }: Props) {
  return (
    <div
      title={mediaTranslations.btn_show_file}
      className={cn(
        "relative w-full flex flex-col justify-between cursor-pointer border-2 rounded border-white p-2 overflow-hidden",
        { "border-blue-500": active },
        { "hover:border-blue-200": !active }
      )}
      onClick={onClick}
    >
      {file.thumbnailUrl ? (
        <img className="w-full h-24 object-contain" src={file.thumbnailUrl} />
      ) : file.type.startsWith("image/") ? (
        <Image className="w-full h-24 flex-none" />
      ) : (
        <FileText className="w-full h-24 flex-none" />
      )}
      <span className="flex-none leading-5 max-h-15 m-auto break-all overflow-hidden">
        {file.name}
      </span>
      {!globalEdit && file.isGlobal && (
        <span
          class="absolute bg-blue-500 text-white rounded-full m-2 p-2"
          title={mediaTranslations.text_file_readonly}
        >
          <Lock class="h-4 w-4" />
        </span>
      )}
    </div>
  );
}
