/*
 * This component renders a subdirectory entry within the current directory
 */
import { Folder, FolderOpen, Lock } from "lucide-preact";
import { useState } from "preact/hooks";
import cn from "classnames";

import { Directory } from "../index";

type Props = {
    directory: Directory;
    onClick?: (event: MouseEvent | KeyboardEvent) => void;
    mediaTranslations: any;
    globalEdit?: boolean;
    allowDrop: boolean;
    itemDropped: () => unknown;
    dragStart: () => unknown;
    dragEnd: () => unknown;
};

const DirectoryEntry = ({
    directory,
    onClick,
    mediaTranslations,
    globalEdit,
    allowDrop,
    itemDropped: fileDropped,
    dragStart,
    dragEnd,
}: Props) => {
    const [isCurrentDropTarget, setIsCurrentDropTarget] = useState(false);

    return (
        <div
            title={mediaTranslations.btn_enter_directory}
            className={cn("relative cursor-pointer hover:text-blue-500 flex flex-col justify-between h-full p-2", {
                "text-blue-500": isCurrentDropTarget,
            })}
            onClick={onClick}
            onKeyDown={onClick}
            onDragOver={(e) => {
                if (allowDrop) {
                    e.preventDefault();
                    setIsCurrentDropTarget(true);
                }
            }}
            onDragLeave={(e) => {
                if (allowDrop) {
                    e.preventDefault();
                    setIsCurrentDropTarget(false);
                }
            }}
            onDrop={(e) => {
                if (allowDrop) {
                    e.preventDefault();
                    setIsCurrentDropTarget(false);
                    fileDropped();
                }
            }}
            onDragStart={dragStart}
            onDragEnd={dragEnd}
            draggable={!allowDrop && (!directory.isGlobal || globalEdit)}>
            {isCurrentDropTarget ? (
                <FolderOpen className="w-full h-24 flex-none" />
            ) : (
                <Folder className="w-full h-24 flex-none" />
            )}
            <span class="font-bold text-black text-center break-all leading-5 max-h-15 m-auto overflow-hidden">
                {directory.name}
            </span>
            {!globalEdit && directory.isGlobal && (
                <span
                    class="absolute bg-blue-500 text-white rounded-full m-2 p-2"
                    title={mediaTranslations.text_dir_readonly}>
                    <Lock class="h-4 w-4" />
                </span>
            )}
        </div>
    );
};
export default DirectoryEntry;
