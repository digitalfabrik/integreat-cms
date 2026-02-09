import { ShortcodeHandle, AcceptArbitraryArguments, PargsDescriptor, KWargsDescriptor } from "./utils";
import type { ToolbarButtonInstanceApi, ContextFormInstanceApi, ContextFormButtonInstanceApi, ContextFormToggleButtonInstanceApi, DialogInstanceApi, DialogData, MenuItemInstanceApi, DialogSpec, BodyComponentSpec } from "../tinymce.d.ts";
import { Editor } from "tinymce";
import { getCsrfToken } from "../../utils/csrf-token";
import { stripProtocol } from "../../utils/url-tools";

function evaluateOnceDecorator<T>(fn: ()=>T): ()=>T {
	let value: T | null = null;
	// Save whether we computed the value as a separate boolean, in case we ever literally compute null
	let computed = false;
	return (): T => {
		if (!computed) {
			value = fn();
			computed = true;
		}
		return value;
	};
};


class PageHandle extends ShortcodeHandle {
	keyword = "page";

	pargs: PargsDescriptor = [
		[["id", "The ID of the page to link to"]],
		[["text", "The text to display (if not specified, show page title)"]],
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

	pageCache: PageCache = null;

	predicate(node: Element): boolean {
		// We also consider old links that look like they point to pages as instances of the page shortcode.
		// This way shortcodes will work on the old links and we will naturally slowly convert content from the old style direct links.
		if (node.nodeName.toLowerCase() === "a") {
			const href = (node as HTMLLinkElement).href;
			if (href && (node as HTMLElement).isContentEditable && this.internalPageURLRegex().exec(href)) {
				return true;
			}
		}
		return super.predicate(node);
	}

	argsFromNode(node: HTMLElement | null): [string[], Map<string, string | undefined>] {
		// If we are operating on an old style direct link, we need to recover what that would be as the arguments for the new shortcode.
		if (node && node.nodeName.toLowerCase() === "a") {
			const [fullURL, path, regionSlug, languageSlug, infix, pageSlug] = node.getAttribute("href").match(this.internalPageURLRegex());
			let text = node.textContent !== node.getAttribute("href") ? node.textContent : "";
			// Get page id for slug
			const translation = this.pageCache.byPath.get(path);
			const id = translation.page.id;
			return [[`${id}`, text], new Map()];
		}
		return super.argsFromNode(node);
	}

	renderPreviewNode(pargs: string[], kwargs: Map<string, string | undefined>): string {
		// The html string representation of the shortcode in the TinyMCE editor
		// By default this is a span marked with mceNonEditable and the shortcode keyword and parameters
		// and defers the visual presented to the user to be rendered to renderPreview()

		// Ensure the data for this is loaded in the cache,
		// including ancestors, so the edit dialog can render the title path
		this.pageCache.requestId(parseInt(pargs[0]), true).then();
		return super.renderPreviewNode(pargs, kwargs)
	}

	renderPreview(pargs: string[], kwargs: Map<string, string | undefined>): string {
		// The html string representation of the shortcode preview in the TinyMCE editor
		// By default this is just the canonical text representation. This function will be overwritten by most subclasses.
		const id = parseInt(pargs[0]);
		const languageSlug = this.tinymceConfig.getAttribute("data-language-slug");
		const page = this.pageCache.byId.get(id);
		// TODO: If page not in cache, re-render after request resolved
		const translation = page?.translations.get(languageSlug);
		const text = pargs[1] || translation?.title;

		const TEXT_MISSING = "MISSING LINK"; // TODO: translations (#4044)
		let element;
		if (!translation) {
			element = document.createElement("i");
			element.classList.add("error");
			element.innerText = `[${text || TEXT_MISSING}]`;
		} else {
			element = document.createElement("a");
			element.innerText = text;
			// No href, the link is non-interactible anyway
			element.href = "#"
		}
		return element.outerHTML;
	}

	async getCompletions(query: string, id: number) {
		const url = this.tinymceConfig.getAttribute("data-link-ajax-url");
		const response = await fetch(url, {
			method: "POST",
			headers: {
				"X-CSRFToken": getCsrfToken(),
			},
			body: JSON.stringify({
				query_string: query,
				object_types: ["event", "page", "poi"],
				archived: false,
				is_link_suggestion: true,
			}),
		});
		const HTTP_STATUS_OK = 200;
		if (response.status !== HTTP_STATUS_OK) {
			return [];
		}

		const data = await response.json();
		return [data.data, id];
	}

	displayEditDialog(initialPargs: string[], initialKWargs: [string, string][]) {
		const ID_ARG = "parg0";
		const TEXT_ARG = "parg1";

		const node = this.getNode();
		const initialText = node ? initialPargs[1] : this.editor.selection.getContent({ format: "text" });

		let prevSearchText = "";
		let prevSelectedCompletion = initialPargs[0] ? initialPargs[0] : "";

		// Stores the current request id, so that outdated requests get ignored
		let ajaxRequestId = 0;
		const defaultCompletionItem = {
			text: this.tinymceConfig.getAttribute("data-link-no-results-text"),
			title: "",
			value: "",
		};
		const languageSlug = this.tinymceConfig.getAttribute("data-language-slug");
		const cachedPageData = this.pageCache.byId.get(parseInt(initialPargs[0])).translations.get(languageSlug);
		const initialCompletionItem = {
			text: cachedPageData.titlePath,
			title: cachedPageData.title,
			value: `${initialPargs[0]}`,
		};
		const completionItems = cachedPageData ? [initialCompletionItem] : [defaultCompletionItem];
		let currentCompletionText = "";

		const that = this;
		const updateDialog = (api: DialogInstanceApi<DialogData>) => {
			super.defaultOnChange(api);

			let data = api.getData();

			let urlChangedBySearch = false;
			// Check if the selected completion changed
			if (prevSelectedCompletion !== data[ID_ARG]) {
				// find the correct text currently shown in the completion items box
				if (completionItems.length > 0) {
					const currentCompletion = completionItems.find(
						(completion) => completion.value === data[ID_ARG]
					);
					// Don't set the completion text to `- no results -`
					if (currentCompletion && currentCompletion.value !== "") {
						currentCompletionText = currentCompletion.title;
					} else {
						currentCompletionText = "";
					}
				} else {
					currentCompletionText = "";
				}
			}
			prevSelectedCompletion = data[ID_ARG];

			// Disable the submit button if no valid page found
			api.setEnabled("submit", data[ID_ARG]);

			// make new ajax request on user input
			if (data.search !== prevSearchText && data.search !== "") {
				ajaxRequestId += 1;
				this.getCompletions(data.search, ajaxRequestId).then(([newCompletions, requestId]) => {
					if (requestId !== ajaxRequestId) {
						return;
					}

					completionItems.length = 0;
					for (const completion of newCompletions) {
						const [fullURL, path, regionSlug, languageSlug, infix, pageSlug] = completion.url.match(that.internalPageURLRegex());
						completionItems.push({
							text: completion.path,
							title: completion.html_title,
							value: `${completion.foreign_object_id}`,
							//value: `${that.pageCache.bySlug.get(languageSlug).get(path).page.id}`,
						});
					}

					let completionDisabled = false;
					if (completionItems.length === 0) {
						completionDisabled = true;
						completionItems.push(defaultCompletionItem);
					}


					// It seems like there is no better way to update the completion list
					/* eslint-disable-next-line @typescript-eslint/no-use-before-define */
					api.redial(dialogConfig);
					api.setData(data);
					api.focus("search");
					prevSearchText = data.search;

					api.setEnabled(ID_ARG, !completionDisabled);

					updateDialog(api);
				});
			} else if (data.search === "" && prevSearchText !== "") {
				// force an update so that the original user url can get restored
				completionItems.length = 0;
				completionItems.push(defaultCompletionItem);
				/* eslint-disable-next-line @typescript-eslint/no-use-before-define */
				api.redial(dialogConfig);
				api.setData(data);
				api.focus("search");
				prevSearchText = data.search;
				//api.disable(ID_ARG);
				updateDialog(api);
			}
		};

		const completion: any = {};
		completion[ID_ARG] = prevSelectedCompletion
		const dialogConfig: DialogSpec<DialogData> = {
			title: this.text(this.editText),
			body: {
				type: "panel",
				items: [
					{
						type: "input",
						name: TEXT_ARG,
						label: this.tinymceConfig.getAttribute("data-link-dialog-text-text"),
						//disabled: textDisabled,
					},
					{
						type: "label",
						label: this.tinymceConfig.getAttribute("data-link-dialog-internal_link-text"),
						items: [
							{
								type: "input",
								name: "search",
							},
							{
								type: "selectbox",
								name: ID_ARG,
								items: completionItems,
								//disabled: true,
							},
						],
					},
				],
			},
			buttons: [
				{
					type: "cancel",
					text: this.tinymceConfig.getAttribute("data-dialog-cancel-text"),
				},
				{
					type: "submit",
					name: "submit",
					text: this.tinymceConfig.getAttribute("data-dialog-submit-text"),
					primary: true,
					enabled: false,
				},
			],
			initialData: {
				...this.defaultInitialData(initialPargs, initialKWargs),
				...completion,
			},
			onSubmit: this.defaultOnSubmit.bind(this),
			onChange: updateDialog.bind(this),
		};

		return this.editor.windowManager.open(dialogConfig);
	}

	populatePageCache() {
		const baseUrl = this.tinymceConfig.getAttribute("data-base-url");
		const regionSlug = this.tinymceConfig.getAttribute("data-region-slug");
		const languageSlug = this.tinymceConfig.getAttribute("data-language-slug");
		const url = `${baseUrl}/api/v3/${regionSlug}/${languageSlug}/pages/`;

		fetch(url, {
			method: "GET",
			headers: {
				"X-CSRFToken": getCsrfToken(),
			},
		}).then((response): any => {
			const HTTP_STATUS_OK = 200;
			if (response.status !== HTTP_STATUS_OK) {
				return [];
			}
			return response.json();
		}).then(async (data) => {
			for (let mainTranslation of data) {
				await this.pageCache.requestId(mainTranslation.page_id);
			};
		});
	}

	setup(editor: Editor) {
		super.setup(editor);

		this.addText = this.tinymceConfig.getAttribute("data-link-dialog-title-text");
		this.editText = this.tinymceConfig.getAttribute("data-link-dialog-title-text");

		const baseUrl = this.tinymceConfig.getAttribute("data-base-url");
		const regionSlug = this.tinymceConfig.getAttribute("data-region-slug");
		const languageSlug = this.tinymceConfig.getAttribute("data-language-slug");
		this.pageCache = new PageCache(baseUrl, regionSlug, languageSlug);

		//this.populatePageCache();
	}
}


class PageCache {
	byId = new Map<number, PageMetadata>();
	byPath = new Map<string, TranslationMetadata>();

	pending = new Map<number, Promise<PageMetadata>>();

	baseUrl: string;
	regionSlug: string;
	defaultLanguageSlug: string;

	_pathRegex = new RegExp(String.raw`
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
	`.replace(/\s+/g, ""));

	constructor(baseUrl: string, regionSlug: string, defaultLanguageSlug: string) {
		this.baseUrl = baseUrl;
		this.regionSlug = regionSlug;
		this.defaultLanguageSlug = defaultLanguageSlug;
	}

	cacheTranslationMetadata(translation: any) {
		const [fullURL, regionSlug, languageSlug, infix, _, slug] = translation.path.match(this._pathRegex);
		console.assert(translation.page_id, `translation without page id:`, translation);

		const pageMetadata = this.byId.get(translation.page_id) || new PageMetadata({
			id: translation.page_id,
			parentId: translation.parent?.id,
			regionSlug: regionSlug,
		}, this);
		if (!this.byId.has(translation.page_id)) {
			this.byId.set(translation.page_id, pageMetadata);
		}

		const translationMetadata = pageMetadata.translations.get(languageSlug) || new TranslationMetadata({
			id: translation.id,
			languageSlug: languageSlug,
			title: translation.title,
			slug: slug,
			path: translation.path,
			page: pageMetadata,
		}, this);
		pageMetadata.translations.set(languageSlug, translationMetadata);

		this.byPath.set(translation.path, translationMetadata);

		return pageMetadata;
	}

	async _getPage(id: number, languageSlug: string = undefined) {
		languageSlug = languageSlug || this.defaultLanguageSlug;

		const url = `${this.baseUrl}/api/v3/${this.regionSlug}/${languageSlug}/page/?id=${id}`;

		const response = await fetch(url, {
			method: "GET",
			headers: {
				"X-CSRFToken": getCsrfToken(),
			},
		})
		const translation = response.status === 200 ? await response.json() : null;
		return {
			id: id,
			languageSlug: languageSlug,
			translation: translation,
		};
	}

	requestId(id: number, ancestors: boolean = false): Promise<PageMetadata> {
		const that = this;
		async function inner(id: number) {
			const {languageSlug, translation} = await that._getPage(id);
			if (!translation) return null;
			const pageMetadata = that.cacheTranslationMetadata(translation);

			for (const [lang, tr] of Object.entries(translation.available_languages)) {
				const {translation} = await that._getPage(id, lang);
				if (translation) {
					that.cacheTranslationMetadata(translation);
				}
			}
			if (ancestors && pageMetadata.parentId) {
				await that.requestId(pageMetadata.parentId, ancestors);
			}
			return pageMetadata;
		}

		if (this.byId.has(id)) {
			// Return a Promise that immediately resolves
			return new Promise((res, rej) => res(this.byId.get(id)));
		} else if (!this.pending.has(id)) {
			// Start a new query
			this.pending.set(id, inner(id));
		}
		// Return the Promise of the ongoing query
		return this.pending.get(id);
	}
}
class PageMetadata {
	_cache: PageCache;

	id: number;
	parentId: number;
	regionSlug: string;
	translations = new Map<string, TranslationMetadata>();

	get parent() {
		return this._cache?.byId.get(this.parentId);
	}

	constructor(data: {id: number, parentId: number, regionSlug: string}, cache: PageCache = null) {
		this._cache = cache;
		this.id = data.id;
		this.parentId = data.parentId;
		this.regionSlug = data.regionSlug;
	}
}

class TranslationMetadata {
	_cache: PageCache;

	id: number;
	languageSlug: string;
	title: string;
	slug: string;
	path: string;
	page: PageMetadata;

	get parent() {
		return this.page.parent?.translations.get(this.languageSlug);
	}
	get titlePath() {
		const reverseTitles = [this.title];
		let translation: TranslationMetadata = this;
		while (translation.page.parentId) {
			translation = translation.parent;
			if (translation) {
				reverseTitles.push(translation.title);
			} else {
				reverseTitles.push("[?]");
				break;
			}
		}
		return reverseTitles.reverse().join(" → ");
	}

	constructor(data: {id: number, languageSlug: string, title: string, slug: string, path: string, page: PageMetadata}, cache: PageCache = null) {
		this._cache = cache;
		this.id = data.id;
		this.languageSlug = data.languageSlug;
		this.title = data.title;
		this.slug = data.slug;
		this.path = data.path;
		this.page = data.page;
	}
}

export default PageHandle;
