/*
 * This component renders a file upload field
 */
import { StateUpdater, useEffect, useRef } from "preact/hooks";
import { FilePlus } from "lucide-preact";
import Dropzone from "dropzone";
import "dropzone/dist/dropzone.css";

import { Directory, MediaApiPaths } from "../index";
import { getCsrfToken } from "../../utils/csrf-token";

type Props = {
    directory: Directory;
    setUploadFile: StateUpdater<boolean>;
    apiEndpoints: MediaApiPaths;
    mediaTranslations: any;
    mediaTypes: { allowedMediaTypes: string };
    submitForm: (event: Event, successCallback: () => void) => any;
    /* eslint-disable-next-line react/no-unused-prop-types */
    isLoading: boolean;
    refreshState: [boolean, StateUpdater<boolean>];
};

const UploadFile = ({
    directory,
    setUploadFile,
    apiEndpoints,
    mediaTranslations,
    mediaTypes,
    submitForm,
    refreshState,
}: Props) => {
    // This state is used to refresh the media library after changes were made
    const [refresh, setRefresh] = refreshState;
    const dropZoneRef = useRef();

    useEffect(() => {
        // We do not want to reload the dropzone itself, so we use a different, local refresh value
        let localRefresh = refresh;
        const dropZone = new Dropzone(dropZoneRef.current, {
            url: apiEndpoints.uploadFile,
            headers: { "X-CSRFToken": getCsrfToken() },
            dictDefaultMessage: mediaTranslations.text_upload_area,
            dictInvalidFileType: `${mediaTranslations.text_error_invalid_file_type} ${mediaTranslations.text_allowed_media_types}`,
            acceptedFiles: `${mediaTypes.allowedMediaTypes}`,
            parallelUploads: 1,
        });
        dropZone.on("queuecomplete", () => {
            const refreshTimeout = 500;
            setTimeout(() => {
                if (dropZone.getAcceptedFiles().length !== 0) {
                    // Refresh directory content
                    setRefresh(!localRefresh);
                    localRefresh = !localRefresh;
                }
            }, refreshTimeout);
            const removalTimeout = 3500;
            setTimeout(() => {
                // Only remove accepted files from the upload area
                dropZone.getAcceptedFiles().forEach((file) => {
                    dropZone.removeFile(file);
                });
            }, removalTimeout);
        });
        return () => dropZone.destroy();
        /* eslint-disable-next-line react-hooks/exhaustive-deps */
    }, []);

    return (
        <div className="flex-auto min-w-0 rounded border border-blue-500 shadow-2xl bg-white">
            <div class="rounded w-full p-4 bg-water-500 font-bold">
                <FilePlus class="inline-block mr-2 h-5" />
                {mediaTranslations.heading_upload_file}
            </div>
            <div className="p-4">
                <form
                    onSubmit={(event: Event) => submitForm(event, () => setUploadFile(false))}
                    action={apiEndpoints.uploadFile}
                    className="dropzone"
                    ref={dropZoneRef}>
                    <input name="parent_directory" type="hidden" value={directory ? directory.id : ""} />
                </form>
            </div>
        </div>
    );
};
export default UploadFile;
