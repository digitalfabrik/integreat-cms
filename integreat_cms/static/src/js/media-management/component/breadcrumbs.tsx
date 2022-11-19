/* eslint react/jsx-key: off */
/*
 * This component renders a breadcrumbs list for the current directory and all its parent directories
 */
import { ChevronRight, Folder, FolderOpen } from "lucide-preact";
import { Link } from "preact-router";
import { useState } from "preact/hooks";

import { Directory } from "../index";

type Props = {
    breadCrumbs: Directory[];
    searchQuery: string;
    mediaTranslations: any;
    allowDrop: boolean;
    dropItem: (targetDirectory: number) => unknown;
};

const Breadcrumbs = ({ breadCrumbs, searchQuery, mediaTranslations, allowDrop, dropItem }: Props) => {
    const [currentDragTarget, setCurrentDragTarget] = useState<null | number>(null);
    return (
        <nav className="p-2">
            <ul class="flex flex-wrap">
                <li
                    className={currentDragTarget === 0 ? "text-blue-600" : ""}
                    onDragOver={(e) => {
                        if (allowDrop) {
                            e.preventDefault();
                            setCurrentDragTarget(0);
                        }
                    }}
                    onDragLeave={(e) => {
                        if (allowDrop) {
                            e.preventDefault();
                            setCurrentDragTarget(null);
                        }
                    }}
                    onDrop={(e) => {
                        if (allowDrop) {
                            e.preventDefault();
                            setCurrentDragTarget(null);
                            dropItem(0);
                        }
                    }}>
                    <Link href="/" className="flex flex-wrap hover:bg-water-600 px-3 py-2 rounded " media-library-link>
                        {allowDrop &&
                            (currentDragTarget === 0 ? <FolderOpen className="mr-2" /> : <Folder className="mr-2" />)}
                        {mediaTranslations.heading_media_root}
                    </Link>
                </li>
                {searchQuery ? (
                    <>
                        <li class="py-2">
                            <ChevronRight />
                        </li>
                        <li class="px-3 py-2">
                            {mediaTranslations.heading_search_results} &ldquo;{searchQuery}&rdquo;
                        </li>
                    </>
                ) : (
                    <>
                        {breadCrumbs.map((directory: Directory) => (
                            <>
                                <li class="py-2">
                                    <ChevronRight />
                                </li>
                                <li
                                    className={currentDragTarget === directory.id ? "text-blue-600" : ""}
                                    onDragOver={(e) => {
                                        if (allowDrop) {
                                            e.preventDefault();
                                            setCurrentDragTarget(directory.id);
                                        }
                                    }}
                                    onDragLeave={(e) => {
                                        if (allowDrop) {
                                            e.preventDefault();
                                            setCurrentDragTarget(null);
                                        }
                                    }}
                                    onDrop={(e) => {
                                        if (allowDrop) {
                                            e.preventDefault();
                                            setCurrentDragTarget(null);
                                            dropItem(directory.id);
                                        }
                                    }}>
                                    <Link
                                        href={`/${directory.id}/`}
                                        class="flex flex-wrap hover:bg-water-600 px-3 py-2 rounded break-all"
                                        media-library-link>
                                        {allowDrop &&
                                            (currentDragTarget === directory.id ? (
                                                <FolderOpen className="mr-2" />
                                            ) : (
                                                <Folder className="mr-2" />
                                            ))}
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
};
export default Breadcrumbs;
