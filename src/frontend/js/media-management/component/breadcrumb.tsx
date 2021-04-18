import { Link } from "preact-router";
import { useEffect, useState } from "preact/hooks";
import { MediaApiPaths } from "..";
import { Directory } from "./directory-listing";

interface Props {
  directoryId: number;
  apiEndpoints: MediaApiPaths;
  mediaTranslations: any;
}

export default function MediacenterBreadcrumb({
  directoryId,
  apiEndpoints,
  mediaTranslations,
}: Props) {
  const [breadCrumbs, setBreadcrumbs] = useState<Directory[]>([]);

  useEffect(() => {
    if (directoryId) {
      (async () => {
        try {
          let url = apiEndpoints.getDirectoryPath;
          url += "?directory=" + directoryId;

          const result = await fetch(url);
          const data = await result.json();

          setBreadcrumbs(data.data);
        } catch (e) {
          console.error(e);
        }
      })();
    } else {
      setBreadcrumbs([]);
    }
  }, [directoryId]);

  return (
    <nav className="p-2">
      <ul class="px-2 p-2 flex text-lg flex-wrap gap-2">
        <li>
          <Link href={`/`}>{mediaTranslations.label_media_root}</Link>
        </li>
        {breadCrumbs.map((directory, i) => (
          <>
            <li>/</li>
            <li>
              <Link href={`/listing/${directory.id}`}>{directory.name}</Link>
            </li>
          </>
        ))}
      </ul>
    </nav>
  );
}
