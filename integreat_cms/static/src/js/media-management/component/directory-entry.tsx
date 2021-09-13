/*
 * This component renders a subdirectory entry within the current directory
 */
import { Folder, Lock } from "preact-feather";

import { Directory } from "../index";
import cn from "classnames";

interface Props {
  directory: Directory;
  onClick?: (event: MouseEvent) => void;
  mediaTranslations: any;
  selectionMode?: boolean;
  globalEdit?: boolean;
}

export default function DirectoryEntry({
  directory,
  onClick,
  mediaTranslations,
  globalEdit,
  selectionMode,
}: Props) {
  return (
    <div
      title={mediaTranslations.btn_enter_directory}
      className={"cursor-pointer hover:text-blue-500 flex flex-col justify-between h-full p-2"}
      onClick={onClick}
    >
      <Folder className={"w-full h-24 flex-none"} />
      <span class="font-bold text-black text-center break-all leading-5 max-h-15 m-auto overflow-hidden">
        {directory.name}
      </span>
      {!selectionMode && !globalEdit && directory.isGlobal && (
        <span
          class="absolute bg-blue-500 text-white rounded-full m-2 p-2"
          title={mediaTranslations.text_dir_readonly}
        >
          <Lock class="h-4 w-4" />
        </span>
      )}
    </div>
  );
}
