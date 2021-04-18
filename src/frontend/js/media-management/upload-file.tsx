import { Link } from "preact-router";
import { useState } from "preact/hooks";
import { getCsrfToken } from "../utils/csrf-token";
import Button from "./component/button";
import { MediaApiPaths } from "./index";
import { route } from "preact-router";

interface Props {
  parentDirectory?: number;
  path?: string;
  apiEndpoints: MediaApiPaths;
  mediaTranslations: any;
}
export default function UploadFile({
  parentDirectory,
  apiEndpoints,
  mediaTranslations,
}: Props) {
  const [uploadFile, setUploadFile] = useState(null);
  const [isLoading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const listingRoute = `/listing/${parentDirectory}`;

  const handleFileUpload = async () => {
    setError(null);
    setLoading(true);
    try {
      const formData = new FormData();
      formData.append("upload", uploadFile);
      formData.append("parentDirectory", parentDirectory.toString());

      const response = await fetch(apiEndpoints.uploadFile, {
        method: "POST",
        headers: {
          "X-CSRFToken": getCsrfToken(),
        },
        body: formData,
      });
      const data = await response.json();
      if (data.error) {
        setError(data.error);
      } else {
        route(listingRoute);
      }
    } catch (e) {}
    setLoading(false);
  };

  return (
    <div className="p-6">
      <div className="w-full max-w-full">
        <div className="header">
          <div className="flex flex-wrap">
            <div>
              <h1 className="heading mb-2">
                {mediaTranslations.btn_upload_file}
              </h1>
            </div>
          </div>
        </div>
      </div>
      <form
        onSubmit={(e) => {
          e.preventDefault();
          handleFileUpload();
        }}
        className="bg-white shadow-md rounded px-8 pt-6 pb-8 mb-4"
      >
        <p className="text-red-400">{error}</p>
        <p>
          <label for="id_name">{mediaTranslations.label_file_name}</label>
          <input
            type="file"
            name="name"
            accept=".png, .jpg, .jpeg, .pdf"
            maxLength={255}
            required
            id="id_name"
            value={uploadFile}
            onChange={({ target }) => setUploadFile((target as any).files[0])}
            className="w-1/2 appearance-none block bg-gray-200 text-gray-600 placeholder-gray-600 border border-gray-200 rounded py-3 pl-4 pr-8 leading-tight focus:outline-none focus:bg-white focus:border-gray-400"
          />
        </p>

        <div className="flex items-center justify-start mt-6">
          <input
            type="submit"
            disabled={isLoading}
            className="bg-blue-500 hover:bg-blue-600 text-white font-bold py-2 px-4 rounded focus:outline-none focus:shadow-outline mr-2 cursor-pointer"
            value={mediaTranslations.btn_submit}
          />
          <Button
            disabled={isLoading}
            href={listingRoute}
            label={mediaTranslations.btn_back}
          />
        </div>
      </form>
    </div>
  );
}
