/* eslint react/button-has-type: 0 */
/*
 * This component renders a sidebar which shows information about the current directory
 * as well as provides the possibility to rename and delete the current directory
 */
import { Save, Sliders, Folder, Edit3, Trash2, Lock } from "lucide-preact";
import { useEffect, useState } from "preact/hooks";
import cn from "classnames";

import { route } from "preact-router";
import { showConfirmationPopupAjax } from "../../confirmation-popups";
import { Directory, MediaApiPaths } from "../index";

type Props = {
    directory: Directory;
    apiEndpoints: MediaApiPaths;
    mediaTranslations: any;
    globalEdit?: boolean;
    submitForm: (event: Event, successCallback?: (data: any) => void) => void;
    isLoading: boolean;
    canDeleteDirectory: boolean;
};
const EditDirectorySidebar = ({
    directory,
    apiEndpoints,
    mediaTranslations,
    globalEdit,
    submitForm,
    isLoading,
    canDeleteDirectory,
}: Props) => {
    // This state is a buffer for the currently changed directory
    const [changedDirectory, setChangedDirectory] = useState<Directory>(directory);
    // This state determines whether the directory name is currently being edited
    const [isDirectoryNameEditable, setDirectoryNameEditable] = useState<boolean>(false);
    // Editing is allowed if either global edit is enabled or the directory is not global
    const isEditingAllowed = globalEdit || !directory.isGlobal;

    useEffect(() => {
        console.debug("Opening sidebar for directory:", directory);
        // Reset changed directory buffer
        setChangedDirectory(directory);
        // Hide input field
        setDirectoryNameEditable(false);
    }, [directory]);

    const onIsHiddenCheckboxClick = () => {
        setChangedDirectory({
            ...changedDirectory,
            isHidden: !changedDirectory.isHidden,
        });
    };

    return (
        <div className="absolute w-full h-full flex flex-col rounded border border-blue-500 bg-white border-solid shadow-2xl">
            <div class="rounded w-full p-4 bg-water-500 font-bold">
                <Sliders class="mr-1 inline-block h-5" />
                {mediaTranslations.heading_directory_properties}
            </div>
            <div className="flex-1 overflow-auto">
                <div class="items-center align-middle w-full">
                    <div class="flex items-center">
                        <Folder className="w-full h-36 align-middle mt-4" />
                    </div>
                </div>
                <form onSubmit={submitForm} action={apiEndpoints.editDirectory} encType="multipart/form-data">
                    <input name="id" type="hidden" value={directory.id} />
                    <div class="flex flex-wrap justify-between gap-2 hover:bg-gray-50 p-4 border-t border-b">
                        <label
                            for="directory-name-input"
                            className={cn("secondary my-0", { "cursor-auto": !isEditingAllowed })}
                            onClick={() =>
                                isEditingAllowed && !isLoading && setDirectoryNameEditable(!isDirectoryNameEditable)
                            }
                            onKeyDown={() =>
                                isEditingAllowed && !isLoading && setDirectoryNameEditable(!isDirectoryNameEditable)
                            }>
                            {mediaTranslations.label_directory_name}
                        </label>
                        {!isDirectoryNameEditable && (
                            <p class="break-all">
                                {directory.name}
                                {isEditingAllowed && (
                                    <button
                                        class="hover:text-blue-500 ml-1 h-5"
                                        onClick={(e) => {
                                            e.preventDefault();
                                            setDirectoryNameEditable(true);
                                        }}
                                        disabled={isLoading}>
                                        <Edit3 class="inline-block" />
                                    </button>
                                )}
                            </p>
                        )}
                        <input
                            id="directory-name-input"
                            name="name"
                            type={isDirectoryNameEditable ? "text" : "hidden"}
                            value={changedDirectory.name}
                            onInput={({ target }) =>
                                setChangedDirectory({
                                    ...changedDirectory,
                                    name: (target as HTMLInputElement).value,
                                })
                            }
                            disabled={isLoading}
                            required
                        />
                    </div>
                    <div class="flex flex-wrap justify-between gap-2 hover:bg-gray-50 p-4 border-b">
                        <label class="secondary my-0">{mediaTranslations.label_directory_created}</label>
                        <p>{directory.CreatedDate}</p>
                    </div>
                    {directory.isGlobal && globalEdit && (
                        <div class="flex flex-wrap justify-between gap-2 p-4 border-b">
                            <label class="secondary my-0" for="directory-hide-input">
                                {mediaTranslations.label_directory_is_hidden}
                            </label>
                            <input
                                id="directory-hide-input"
                                name="is_hidden"
                                type="checkbox"
                                value={String(changedDirectory.isHidden)}
                                checked={changedDirectory.isHidden}
                                onClick={() => {
                                    onIsHiddenCheckboxClick();
                                }}
                            />
                        </div>
                    )}
                    <div class="p-4">
                        {isEditingAllowed ? (
                            <div class="flex flex-col gap-4">
                                {(isDirectoryNameEditable || changedDirectory.isHidden !== directory.isHidden) && (
                                    <button
                                        title={mediaTranslations.btn_change_directory}
                                        class="btn"
                                        type="submit"
                                        disabled={isLoading}>
                                        <Save class="mr-1 inline-block h-5" />
                                        {mediaTranslations.btn_change_directory}
                                    </button>
                                )}
                                {canDeleteDirectory && (
                                    <button
                                        title={
                                            directory.numberOfEntries === 0
                                                ? mediaTranslations.btn_delete_directory
                                                : mediaTranslations.btn_delete_empty_directory
                                        }
                                        className={cn("btn", {
                                            "btn-red": !isLoading && directory.numberOfEntries === 0,
                                        })}
                                        data-confirmation-title={mediaTranslations.text_dir_delete_confirm}
                                        data-confirmation-subject={directory.name}
                                        disabled={isLoading || directory.numberOfEntries !== 0}
                                        onClick={showConfirmationPopupAjax}
                                        onaction-confirmed={() => document.getElementById("delete-directory").click()}>
                                        <Trash2 class="mr-2 inline-block h-5" />
                                        {mediaTranslations.btn_delete_directory}
                                    </button>
                                )}
                            </div>
                        ) : (
                            <p class="italic">
                                <Lock class="mr-1 inline-block h-5" />
                                {mediaTranslations.text_dir_readonly}
                            </p>
                        )}
                    </div>
                </form>
                {/* Hidden form for directory deletion (on success, redirect to parent directory) */}
                <form
                    onSubmit={(event: Event) =>
                        submitForm(event, () => route(`${directory.parentId && "/"}${directory.parentId}/`))
                    }
                    action={apiEndpoints.deleteDirectory}
                    class="hidden">
                    <input name="id" type="hidden" value={directory.id} />
                    <button id="delete-directory" aria-label="delete directory" />
                </form>
            </div>
        </div>
    );
};
export default EditDirectorySidebar;
