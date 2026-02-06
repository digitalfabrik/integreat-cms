import { ShortcodeHandle, AcceptArbitraryArguments, PargsDescriptor, KWargsDescriptor } from "./utils";
import type { ToolbarButtonInstanceApi, ContextFormInstanceApi, ContextFormButtonInstanceApi, ContextFormToggleButtonInstanceApi, DialogInstanceApi, DialogData, MenuItemInstanceApi, DialogSpec, BodyComponentSpec } from "../tinymce.d.ts";
import { Editor } from "tinymce";
import { getCsrfToken } from "../../utils/csrf-token";

type TranslationMetadata = {id: number, parent: number, regionSlug: string, translations: Map<string, {id: number, languageSlug: string, title: string, slug: string}>};

function stripProtocol(url: string) {
	return url.replace(/^[^:/]*:\/\//, "");
}

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

	editText = "";
	
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

	pageCache = new PageCache();

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
			const translation = this.pageCache.bySlug.get(languageSlug).get(path);
			const id = translation.id;
			return [[`${id}`, text], new Map()];
		}
		return super.argsFromNode(node);
	}

	renderPreviewNode(pargs: string[], kwargs: Map<string, string | undefined>): string {
		// The html string representation of the shortcode in the TinyMCE editor
		this.prefetchPageById(parseInt(pargs[0]));
		return super.renderPreviewNode(pargs, kwargs)
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
		const cachedPageData = this.pageCache.byId.get(parseInt(initialPargs[0])).get(languageSlug);
		const initialCompletionItem = {
			text: cachedPageData.path,
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
					if (currentCompletion.value !== "") {
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
							//value: `${that.pageCache.bySlug.get(languageSlug).get(path).pageId}`,
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

	prefetchPageById(id: number) {
		if (!id) return;

		// todo: prevent duplicates

		const baseUrl = this.tinymceConfig.getAttribute("data-base-url");
		const regionSlug = this.tinymceConfig.getAttribute("data-region-slug");
		const languageSlug = this.tinymceConfig.getAttribute("data-language-slug");
		const url = `${baseUrl}/api/v3/${regionSlug}/${languageSlug}/page/?id=${id}`;

		fetch(url, {
			method: "GET",
			headers: {
				"X-CSRFToken": getCsrfToken(),
			},
		}).then((response): any => {
			const HTTP_STATUS_OK = 200;
			if (response.status !== HTTP_STATUS_OK) {
				return {};
			}
			return response.json();
		}).then(translation => {
			this.pageCache.cacheTranslationMetadata(languageSlug, translation, translation.page_id);
			Object.entries(translation.available_languages).forEach(([lang, tr]) => {
				this.pageCache.cacheTranslationMetadata(lang, tr, translation.page_id);
			});
			console.log(this.pageCache);
		});
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
		}).then(data => {
			data.forEach((translation: any) => {
				this.pageCache.cacheTranslationMetadata(languageSlug, translation, translation.page_id);
				Object.entries(translation.available_languages).forEach(([lang, tr]) => {
					this.pageCache.cacheTranslationMetadata(lang, tr, translation.page_id);
				});
			});
		});
	}

	setup(editor: Editor) {
		super.setup(editor);
		//this.populatePageCache();

		this.editText = this.tinymceConfig.getAttribute("data-link-dialog-title-text");
	}
}


class PageCache {
	bySlug = new Map<string, TranslationMetadata>();
	byId = new Map<number, TranslationMetadata>();

	pending = new Map<number, Promise>();

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
	`.replace(/\s+/g, "")));

	constructor(baseUrl: string, regionSlug: string, defaultLanguageSlug: string) {
		this.baseUrl = baseUrl;
		this.regionSlug = regionSlug;
		this.defaultLanguageSlug = defaultLanguageSlug;
	}

	cacheTranslationMetadata(translation: any) {
		pageId = pageId || translation.page_id;
		const [regionSlug, languageSlug, infix, _, slug] = translation.path.match(that._pathRegex);

		const metadata = this.byId.get(pageId) || {
			id: pageId,
			parent: translation.parent.id,
			regionSlug: regionSlug,
			translations: new Map<string, {id: number, languageSlug: string, title: string, slug: string, path: string},
		};
		if (!this.byId.has(pageId)) {
			this.byId.set(pageId, metadata);
		}

		if (!this.bySlug.has(languageSlug)) {
			this.bySlug.set(languageSlug, new Map());
		}
		this.bySlug.get(languageSlug).set(translation.path, metadata);

		metadata.translations.set(languageSlug, {
			id: translation.id,
			languageSlug: languageSlug,
			title: translation.title,
			slug: slug,
			path: translation.path,
		});

		return metadata;
	}

	requestId(id: number): Promise {
		async function inner(id: number) {
			const url = `${this.baseUrl}/api/v3/${this.regionSlug}/${this.defaultLanguageSlug}/page/?id=${id}`;

			const response = await fetch(url, {
				method: "GET",
				headers: {
					"X-CSRFToken": getCsrfToken(),
				},
			})
			const HTTP_STATUS_OK = 200;
			if (response.status !== HTTP_STATUS_OK) {
				return {};
			}
			const translation = await response.json();
			const metadata = this.cacheTranslationMetadata(languageSlug, translation, translation.page_id);
			Object.entries(translation.available_languages).forEach(([lang, tr]) => {
				this.cacheTranslationMetadata(lang, tr, translation.page_id);
			});
			return metadata;
		}

		if (this.byId.has(id)) {
			// Return a Promise that immediately resolves
			return new Promise((res, rej) => res(this.byId.get(id)));
		} else if (!this.pending.has(id)) {
			// Start a new query
			this.pending.set(id, inner(id, languageSlug));
		}
		// Return the Promise of the ongoing query
		return this.pending.get(id);
	}
}

export default PageHandle;
