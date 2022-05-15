/*
 * This component renders a breadcrumbs list for the current directory and all its parent directories
 */
import { ChevronRight } from "preact-feather";
import { Link } from "preact-router";
import { useState } from "preact/hooks";

import { Directory } from "../index";

interface Props {
  breadCrumbs: Directory[];
  searchQuery: string;
  mediaTranslations: any;
  allowDrop: boolean;
  dropItem: (targetDirectory: number) => unknown;
}

export default function Breadcrumbs({ breadCrumbs, searchQuery, mediaTranslations,allowDrop, dropItem, }: Props) {
  const [currentDragTarget, setCurrentDragTarget] = useState<null|number>(null);
  return (
    <nav className={allowDrop ? "p-2 text-red-400" :"p-2"}>
      <ul class="flex flex-wrap">
        <li className={currentDragTarget === 0 ? 'text-green-400' : ''} onDragOver={(e) => {
          if(allowDrop) {
            e.preventDefault();
            setCurrentDragTarget(0)
          }
        }} onDragLeave={
          e => {if(allowDrop) {
            e.preventDefault();
            setCurrentDragTarget(null)
          }}
          
        }
        onDrop={
          e => {if(allowDrop) {
            e.preventDefault();
            setCurrentDragTarget(null)
            dropItem(0);
          }}}
        >
          <Link href={"/"} className={"block hover:bg-water-600 px-3 py-2 rounded"} media-library-link>
            {mediaTranslations.heading_media_root}
          </Link>
        </li>
        {searchQuery ? (
          <>
            <li class="py-2">
              <ChevronRight />
            </li>
            <li class="px-3 py-2">
              {mediaTranslations.heading_search_results} "{searchQuery}"
            </li>
          </>
        ) : (
          <>
            {breadCrumbs.map((directory: Directory) => (
              <>
                <li class="py-2">
                  <ChevronRight />
                </li>
                <li className={currentDragTarget === directory.id ? 'text-green-400' : ''} onDragOver={(e) => {
          if(allowDrop) {
            e.preventDefault();
            setCurrentDragTarget(directory.id)
          }
        }} onDragLeave={
          e => {if(allowDrop) {
            e.preventDefault();
            setCurrentDragTarget(null)
          }}
          
        }
        onDrop={
          e => {if(allowDrop) {
            e.preventDefault();
            setCurrentDragTarget(null)
            dropItem(directory.id);
          }}}>
                  <Link
                    href={`/${directory.id}/`}
                    class="block hover:bg-water-600 px-3 py-2 rounded break-all"
                    media-library-link
                  >
                    {directory.name}
                  </Link>
                </li>
              </>
            ))}
          </>
        )}
      </ul>
    </nav>
  );
}
