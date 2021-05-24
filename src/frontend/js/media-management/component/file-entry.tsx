import { File as FileIcon } from "preact-feather";
import { File } from "./directory-listing";
import cn from "classnames";
interface Props {
  item: File;
  active: boolean;
  onClick: (event: MouseEvent) => void;
}
export default function FileEntry({ item, active, onClick }: Props) {
  return (
    <div
      className={cn("flex flex-col items-center h-44 w-44 cursor-pointer", {
        "border-2 border-blue-900 rounded": active,
      })}
      onClick={onClick}
    >
      {item.thumbnailPath ? (
        <img className="h-24 w-3/4 object-contain" src={item.thumbnailPath} />
      ) : (
        <FileIcon className="w-full h-24" />
      )}
      <div className="flex-1"></div>
      <span class="align-baseline">{item.name}</span>
    </div>
  );
}
