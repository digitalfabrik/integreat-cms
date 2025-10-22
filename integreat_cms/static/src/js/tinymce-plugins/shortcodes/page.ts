import { ShortcodeHandle, AcceptArbitraryArguments, PargsDescriptor, KWargsDescriptor } from "./utils";

class PageHandle extends ShortcodeHandle {
	keyword = "page";

	pargs: PargsDescriptor = [
		[["id", "The ID of the page to link to"]],
		[["text", "The text to display (if not specified, show page title)"]],
	];
	kwargs: KWargsDescriptor = [];
}


export default PageHandle;
