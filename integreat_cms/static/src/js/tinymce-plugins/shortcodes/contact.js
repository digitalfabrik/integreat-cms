import { ShortcodeHandle } from "./utils";

class ContactHandle extends ShortcodeHandle {
	keyword = "contact";
	addIcon = "contact";
	editIcon = "contact";
	removeIcon = "remove";

	pargs = [2, 8];
	kwargs = ["one", "two"];
}


export default ContactHandle;
