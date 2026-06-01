import { ShortcodeHandle, AcceptArbitraryArguments, PargsDescriptor, KWargsDescriptor } from "./utils";
import type { ToolbarButtonInstanceApi, ContextFormInstanceApi, ContextFormButtonInstanceApi, ContextFormToggleButtonInstanceApi, DialogInstanceApi, DialogData, MenuItemInstanceApi, DialogSpec, BodyComponentSpec } from "../tinymce.d.ts";
import { Editor } from "tinymce";
import TomSelect from "tom-select";
import { getCsrfToken } from "../../utils/csrf-token";
import { stripProtocol } from "../../utils/url-tools";
import { evaluateOnceDecorator } from "../../utils/caching-functions";

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

	domainAndPrefix: () => string = evaluateOnceDecorator(() => stripProtocol(this.tinymceConfig.getAttribute("data-webapp-url")));
	// Regular expression to check íf a link could be a page
	// Capture groups: Path, Region slug, language slug, page infix, page slug
	internalPageURLRegex: () => RegExp = evaluateOnceDecorator(() => new RegExp(String.raw`
		^[^:/]*://
		${this.domainAndPrefix().replace(/\/$/, "")}
		(
			/
			([^/]+)
			/
			([^/]{2,8})
			/
			(
				([^?#]+)
				/
			)?
			([^/?#]+)
		)
	`.replace(/\s+/g, "")));

	//contactCache: ContactCache = null;

	predicate(node: Element): boolean {
		// We also consider old contact cards as instances of the contact shortcode.
		// This way shortcodes will work on the old contact cards and we will naturally slowly convert content from the old style directly embedded HTML.
		if ("contactId" in (node as HTMLElement).dataset) {
			return true;
		}
		return super.predicate(node);
	}

	setup(editor: Editor): boolean {
		super.setup(editor);

		this.addText = this.tinymceConfig.getAttribute("data-contact-menu-text");
		this.editText = this.tinymceConfig.getAttribute("data-contact-change-text");
		this.removeText = this.tinymceConfig.getAttribute("data-contact-remove-text");

		const isContactsEnabled = this.tinymceConfig.getAttribute("data-contact-module-activated") !== "False";
		if (!isContactsEnabled) {
			return false;
		}
		return true;
	}
}


export default ContactHandle;
