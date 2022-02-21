/*
 * This component renders a breadcrumbs list for the current directory and all its parent directories
 */
import { ChevronRight } from "preact-feather";
import { Link } from "preact-router";

import { Directory } from "../index";

interface Props {
  breadCrumbs: Directory[];
  searchQuery: string;
  mediaTranslations: any;
}

export default function Breadcrumbs({ breadCrumbs, searchQuery, mediaTranslations }: Props) {
  return (
    <nav className="p-2">
      <ul class="flex flex-wrap">
        <li>
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
                <li>
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
