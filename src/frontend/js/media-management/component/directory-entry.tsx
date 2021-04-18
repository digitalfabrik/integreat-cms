import { Folder } from "preact-feather";
import { Directory } from "./directory-listing";

interface Props {
  item: Directory;
  onClick?: (event: MouseEvent) => void;
}
export default function DirectoryEntry({ item, onClick }: Props) {
  return (
    <div
      className="flex flex-col items-center h-full cursor-pointer"
      onClick={onClick}
    >
      <Folder className="w-full h-24" />
      <div className="flex-1"></div>
      <span>{item.name}</span>
    </div>
  );
}
