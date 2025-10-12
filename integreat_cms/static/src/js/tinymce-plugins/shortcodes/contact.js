import { ShortcodeHandle } from "./utils";

class ContactHandle extends ShortcodeHandle {
	keyword = "contact";
	addIcon = "contact";
	editIcon = "contact";
	removeIcon = "remove";

	pargs = [2, 8];
	kwargs = ["one", ["etc", false], "two", ["opt", false]];
}


export default ContactHandle;
