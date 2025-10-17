import { ShortcodeHandle, AcceptArbitraryArguments } from "./utils";

class ContactHandle extends ShortcodeHandle {
	keyword = "contact";
	addIcon = "contact";
	editIcon = "contact";
	removeIcon = "remove";

	pargs = [2, 8];
	kwargs = ["one", ["etc", false, "The id "], "two", ["opt", false], AcceptArbitraryArguments];
}


export default ContactHandle;
