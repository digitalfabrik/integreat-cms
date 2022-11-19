/*
 * This component renders a form to create a new directory
 */
import { route } from "preact-router";
import { FolderPlus } from "lucide-preact";
import { StateUpdater } from "preact/hooks";
import { MediaApiPaths } from "../index";

type Props = {
    parentDirectoryId: string;
    apiEndpoints: MediaApiPaths;
    mediaTranslations: any;
    submitForm: (event: Event, successCallback: (data: any) => void) => void;
    isLoading: boolean;
    setCreateDirectory: StateUpdater<boolean>;
};
const CreateDirectory = ({
    parentDirectoryId,
    apiEndpoints,
    mediaTranslations,
    submitForm,
    isLoading,
    setCreateDirectory,
}: Props) => (
    <div className="flex-auto rounded border border-blue-500 shadow-2xl bg-white">
        <div class="rounded w-full p-4 bg-water-500 font-bold">
            <FolderPlus class="inline-block mr-2 h-5" />
            {mediaTranslations.heading_create_directory}
        </div>
        <form
            onSubmit={(event: Event) =>
                // Redirect to new created directory on success
                submitForm(event, (data: any) => {
                    setCreateDirectory(false);
                    route(`/${data.directory.id}/`);
                })
            }
            action={apiEndpoints.createDirectory}
            className="p-4">
            <input name="parent" type="hidden" value={parentDirectoryId} />
            <label for="create-directory-name-input">{mediaTranslations.label_directory_name}</label>
            <div class="flex flex-row gap-2 pt-2">
                <input
                    id="create-directory-name-input"
                    type="text"
                    name="name"
                    maxLength={255}
                    placeholder={mediaTranslations.text_enter_directory_name}
                    disabled={isLoading}
                    required
                />
                <button disabled={isLoading} class="btn" type="submit">
                    {mediaTranslations.btn_create}
                </button>
            </div>
        </form>
    </div>
);
export default CreateDirectory;
