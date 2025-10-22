import { ShortcodeHandle, AcceptArbitraryArguments, PargsDescriptor, KWargsDescriptor } from "./utils";

class ContactHandle extends ShortcodeHandle {
	keyword = "contact";
	addIcon = "contact";
	editIcon = "contact";
	removeIcon = "remove";

	pargs: PargsDescriptor = [
		[["Contact ID", "The ID of the Contact whose details should be displayed"]],
		[
			["address", "Whether the address should be shown and other, not explicitly wanted details should be hidden"],
			["email", "Whether the email should be shown and other, not explicitly wanted details should be hidden"],
			["phone_number", "Whether the phone number should be shown and other, not explicitly wanted details should be hidden"],
			["mobile_phone_number", "Whether the mobile phone number should be shown and other, not explicitly wanted details should be hidden"],
			["website", "Whether the website should be shown and other, not explicitly wanted details should be hidden"],
		],
	];
	kwargs: KWargsDescriptor = [];
}


export default ContactHandle;
