/*
 * This component renders a breadcrumbs list for the current directory and all its parent directories
 */
import { Link } from "preact-router";

import { Directory } from "../index";

interface Props {
  breadCrumbs: Directory[];
  mediaTranslations: any;
}

export default function Breadcrumbs({ breadCrumbs, mediaTranslations }: Props) {
  return (
    <nav className="p-2">
      <ul class="flex flex-wrap gap-2">
        <li>
          <Link href={"/"} className={"block hover:bg-blue-600 px-3 py-2 rounded"}>
            {mediaTranslations.heading_media_root}
          </Link>
        </li>
        {breadCrumbs.map((directory: Directory) => (
          <>
            <li class={"py-2"}>/</li>
            <li>
              <Link
                href={`/${directory.id}/`}
                className={"block hover:bg-blue-600 px-3 py-2 rounded break-all"}
                media-library-link
              >
                {directory.name}
              </Link>
            </li>
          </>
        ))}
      </ul>
    </nav>
  );
}
