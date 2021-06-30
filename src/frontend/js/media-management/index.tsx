/*
 * This file contains the entrypoint for the media library preact component.
 *
 * Documentation of preact: https://preactjs.com/
 *
 * The directory id is injected from the url into the preact component via preact router:
 * https://github.com/preactjs/preact-router
 */
import { render, h } from "preact";
import { useState } from "preact/hooks";
import Router from "preact-router";
import { createHashHistory } from "history";
import cn from "classnames";

import MessageComponent, { Message } from "./component/message";
import Library from "./library";

export interface MediaApiPaths {
  getDirectoryPath: string;
  getDirectoryContent: string;
  createDirectory: string;
  editDirectory: string;
  deleteDirectory: string;
  uploadFile: string;
  editFile: string;
  deleteFile: string;
}

export interface File {
  id: number;
  name: string;
  url: string | null;
  path: string | null;
  altText: string;
  type: string;
  typeDisplay: string;
  thumbnailUrl: string | null;
  uploadedDate: Date;
  isGlobal: boolean;
}

export interface Directory {
  id: number;
  name: string;
  parentId: string;
  numberOfEntries: number;
  CreatedDate: Date;
  isGlobal: boolean;
  type: "directory";
}

export type MediaLibraryEntry = Directory | File;

interface Props {
  apiEndpoints: MediaApiPaths;
  mediaTranslations: any;
  globalEdit?: boolean;
  expertMode?: boolean;
  allowedMediaTypes?: string;
  selectionMode?: boolean;
  selectMedia?: (file: File) => any;
}

export default function MediaManagement(props: Props) {
  // This state can be used to show a success or error message
  const [newMessage, showMessage] = useState<Message | null>(null);
  // This state is a semaphore to block actions while an ajax call is running
  const [isLoading, setLoading] = useState<boolean>(false);

  return (
    <div className={cn("flex flex-col flex-grow min-w-0", { "cursor-wait": isLoading })}>
      <MessageComponent newMessage={newMessage} />
      <Router history={createHashHistory() as any}>
        <Library
          path="/:directoryId?"
          showMessage={showMessage}
          loadingState={[isLoading, setLoading]}
          {...props}
        />
      </Router>
    </div>
  );
}

document.addEventListener("DOMContentLoaded", () => {
  document.querySelectorAll("integreat-media-management").forEach((el) => {
    const mediaConfigData = JSON.parse(document.getElementById("media_config_data").textContent);
    render(
      <MediaManagement
        {...mediaConfigData}
        globalEdit={el.hasAttribute("data-enable-global-edit")}
      />,
      el
    );
  });
  // mark all non-media-library-links as "native" so they are routed by the browser instead of preact
  document.querySelectorAll("a:not([media-library-link])").forEach((link) => {
    link.setAttribute("native", "");
  });
});

(window as any).IntegreatMediaManagement = MediaManagement;
(window as any).preactRender = render;
(window as any).preactJSX = h;
