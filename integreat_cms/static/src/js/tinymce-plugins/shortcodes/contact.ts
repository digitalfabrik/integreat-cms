import { ShortcodeHandle, AcceptArbitraryArguments, PargsDescriptor, KWargsDescriptor } from "./utils";

class ContactHandle extends ShortcodeHandle {
	keyword = "contact";
	addIcon = "contact";
	editIcon = "contact";
	removeIcon = "remove";

	pargs: PargsDescriptor = [
		["first", ["second", "very descriptive"]],
		[["third", "such wow"], "fourth"],
	];
	kwargs: KWargsDescriptor = ["one", ["etc", true, "The id ", "e.t.C."], "two", ["opt", false], AcceptArbitraryArguments];
}


export default ContactHandle;
