/// <reference path="../tinymce.d.ts" />
import type { ContextFormInstanceApi, ContextFormButtonInstanceApi, ContextFormToggleButtonInstanceApi, DialogInstanceApi, DialogData, MenuItemInstanceApi, DialogSpec, BodyComponentSpec } from "../tinymce.d.ts";
import { Editor } from "tinymce";

import type { Parser } from "./shortcodes";
import { Shortcode as parser } from "./shortcodes";

/*

- enable easily implementing behaviour to edit/manage different kinds of shortcodes
- register handle() function to parse shortcode arguments into tinymce readable marker
- ??? provide function to get canocical shortcode ???  (to be used when turning markers back into just the shortcode)
- provide easily overrideable methods for UI handling

- one ShortcodeHandle object per shortcode type, not per shortcode in content

*/


type TextDescriptor = string | ((self: ShortcodeHandle) => string);
/* Positional arguments:
 * - number:            How many positional arguments have to be given (exactly, not more and not less)
 * - [number, number]:  Up to how many positional arguments CAN be given, and how many of those are required
 * - null:              Allow any number of positional arguments
 * Keyword arguments:
 * - (string | [string, boolean])[]:  List of all keyword arguments being accepted.
 *                                    If an item is given as a list where the second value is true, the keyword is required.
 *                                    Also serves as a canonical order normalizing the shortcode
 * - null:                            Allow any keyword argument
 */
type PargsConstraint = number | [number, number] | null;
type KWargsDescriptor = (string | [string, boolean])[] | null;


class ShortcodeHandle {
    keyword: string;
    endword: string | null = null;
    editor: Editor;
    tinymceConfig: HTMLElement;
    addText: TextDescriptor = (self: ShortcodeHandle) => `Insert ${self.keyword}`;
    addIcon: string = "link";
    editText: TextDescriptor = (self: ShortcodeHandle) => `Edit ${self.keyword}`;
    editIcon: string = "link";
    removeText: TextDescriptor = (self: ShortcodeHandle) => `Remove ${self.keyword}`;
    removeIcon: string = "unlink";

    static escape() {
        return (str: string): string => str.includes(" ") ? `"${str.replace(/"/g, '\\"')}"` : str;
    }

    pargs: PargsConstraint = null;
    kwargs: KWargsDescriptor = null;
    get maxPargs() {
        return this.pargs === null ? Infinity : (typeof this.pargs === "number" ? this.pargs : this.pargs[0]);
    }
    get minPargs() {
        return this.pargs === null ? 0        : (typeof this.pargs === "number" ? this.pargs : this.pargs[1]);
    }

    text(text: TextDescriptor): string {
        if (typeof text === "string") {
            return text;
        }
        return text(this);
    }

    predicate(node: Element): boolean {
        if (!(node instanceof HTMLElement)) return false;
        return "shortcode" in node.dataset && node.dataset.shortcode == this.keyword;
    }

    getNode(): HTMLElement | null {
        const node = this.editor.selection.getNode();
        return this.predicate(node) ? node : null;
    };

    sortKWargs(kwpairs: [string, string][]): [string, string][] {
        const order = this.kwargs !== null ? this.kwargs.map(kw => typeof kw === "string" ? kw : kw[0]) : [];
        return kwpairs.sort((a, b) => {
            const aPos = order.includes(a[0]) ? order.indexOf(a[0]) : order.length;
            const bPos = order.includes(b[0]) ? order.indexOf(b[0]) : order.length;
            return aPos - bPos;
        });
    }

    renderShortcode(pargs: string[], kwargs: Map<string, string>): string {
        const pairs = this.sortKWargs(Object.entries(kwargs)).map(pair => pair.map(escape).join("="));
        const parts = [escape(this.keyword), ...pargs.map(escape), ...pairs];
        return `[${parts.join(" ")}]`;
    }

    renderPreview(pargs: string[], kwargs: Map<string, string>): string {
        const ppairs = pargs.map((arg, i) => `data-parg${i}="${arg}"`);
        const kwpairs = this.sortKWargs(Object.entries(kwargs)).map(([key, value]) => `data-kw-${key}=${escape(value)}`);
        const parts = [`class="mceNonEditable"`, `data-shortcode="${this.keyword}"`, ...ppairs, ...kwpairs];
        return `<span ${parts.join(" ")}>${this.renderShortcode(pargs, kwargs)}</span>`;
    }

    openEditDialog(formApi: MenuItemInstanceApi | ContextFormInstanceApi) {
        const node = this.getNode();

        const initialPargs = node !== null ? node.dataset.pargs.split(" ") : [];
        while (initialPargs.length < this.minPargs) {
            initialPargs.push("");
        }

        const prefix = "data-kw-";
        const initialKWargs = this.sortKWargs(Object.entries(node !== null ? node.dataset : {}).reduce((acc, pair) => {
            if (pair[0].startsWith(prefix)) {
                const keyword = pair[0].slice(prefix.length);
                acc.push([keyword, pair[1]]);
            }
            return acc;
        }, []));

        initialPargs.push("8");
        initialKWargs.push(["test", "3"])

        const argumentItems: BodyComponentSpec[] = [];
        initialPargs.forEach((parg: string, i: number) => {
            argumentItems.push({
                type: "input",
                name: `parg${i}`,
                label: `Argument ${i}`,
            });
        });
        if (this.minPargs != this.maxPargs) {
            argumentItems.push({
                type: "bar",
                items: [
                    {
                        type: "button",
                        text: "–",
                        name: "parg-remove",
                    },
                    {
                        type: "button",
                        text: "+",
                        name: "parg-add",
                    },
                ],
            });
        }
        initialKWargs.forEach(([keyword, value]: [string, string], i: number) => {
            if (this.kwargs === null) {
                argumentItems.push({
                    type: "bar",
                    items: [
                        {
                            type: "input",
                            name: `kwarg${i}-name`,
                            label: `Keyword argument ${i}`,
                        },
                        {
                            type: "input",
                            name: `kwarg${i}-value`,
                            label: `Value`,
                        },
                    ],
                });
            } else {
                argumentItems.push({
                    type: "input",
                    name: `kw-${keyword}`,
                    label: `${keyword.slice(0,1).toUpperCase()}${keyword.slice(1).replace("-", " ")}`,
                });
            }
        });
        if (this.kwargs === null) {
            argumentItems.push({
                type: "bar",
                items: [
                    {
                        type: "button",
                        text: "–",
                        name: "kwarg-remove",
                    },
                    {
                        type: "button",
                        text: "+",
                        name: "kwarg-add",
                    },
                ],
            });
        }

        const dialogConfig: DialogSpec<DialogData> = {
            title: this.text(this.editText),
            body: {
                type: "panel",
                items: argumentItems,
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
                },
            ],
            initialData: {
                ...Object.fromEntries(initialPargs.map((parg: string, i: number) => [`parg${i}`, parg])),
                ...Object.fromEntries(initialKWargs.reduce((acc, [keyword, value], i) => {
                    if (this.kwargs === null) {
                        return acc.concat([
                            [`kwarg${i}-name`, keyword],
                            [`kwarg${i}-value`, value],
                        ]);
                    } else {
                        return acc.concat([
                            [`kw-${keyword}`, value],
                        ]);
                    }
                }, [])),
            },
            onSubmit: (api: DialogInstanceApi<DialogData>) => {
                const data = api.getData();
                const pargs = Object.entries(data).reduce((acc: string[], [key, value]) => {
                    const match = key.match(/^parg([0-9]+)$/);
                    if (match) {
                        acc[parseInt(match[1])] = value;
                    }
                    return acc;
                }, []);
                type TemporaryPairs = {[key: number]: [null | string, null | string]};
                type FinalizedPairs = {[key: string]: string};
                const kwargs = Object.entries(data).reduce((acc: TemporaryPairs & FinalizedPairs, [key, value]) => {
                    // First piece together the names with the values again
                    const match = key.match(/^(kw-(.+)|kwarg([0-9]+)-(name|value))$/);
                    if (match) {
                        if (match[2]) {
                            acc[match[2]] = value;
                        } else {
                            const id = parseInt(match[3]);
                            const which = match[4] == "name" ? 0 : 1;
                            if (acc[id] === undefined)  acc[id] = [null, null];
                            acc[id][which] = value;
                            if (acc[id][(which+1) % 2] !== null) {
                                // Pair is complete!
                                [key, value] = acc[id];
                                acc[key] = value;
                                delete acc[id];
                            }
                        }
                    }
                    return acc;
                }, {}) as unknown as FinalizedPairs;

                if (pargs.length <= this.minPargs || pargs.length >= this.maxPargs) {
                    return;
                }
                api.close();

                // Either insert a new shortcode or update the existing one
                const node = this.getNode();
                if (!node) {
                    this.editor.insertContent(this.renderShortcode(pargs, new Map(Object.entries(kwargs))));
                } else {
                    node.remove();
                    this.editor.insertContent(this.renderShortcode(pargs, new Map(Object.entries(kwargs))));
                }
            },
            //onChange: updateDialog,
        };
        console.log(`[${this.keyword}]`, this, dialogConfig);

        return this.editor.windowManager.open(dialogConfig);
    }

    setup(editor: Editor) {
        /* default behavior:
         * - menu item to insert shortcode → open dialog
         * - context toolbar with edit and delete
         */
        this.editor = editor;
        this.tinymceConfig = document.getElementById("tinymce-config-options");

        const closeContextToolbar = () => {
            editor.fire("contexttoolbar-hide", {
                toolbarKey: `shortcode_${this.keyword}_context_form`,
            });
        };

        editor.ui.registry.addMenuItem(`add_shortcode_${this.keyword}`, {
            text: this.text(this.addText),
            icon: this.addIcon,
            onAction: this.openEditDialog.bind(this),
        });

        // This form opens when a shortcode is currently selected with the cursor
        editor.ui.registry.addContextForm(`shortcode_${this.keyword}_context_form`, {
            predicate: this.predicate.bind(this),
            position: "node",
            scope: "node",
            commands: [
                {
                    type: "contextformbutton",
                    icon: this.editIcon,
                    text: this.text(this.editText),
                    tooltip: this.text(this.editText),
                    primary: true,
                    onAction: ((formApi: ContextFormInstanceApi, api: ContextFormButtonInstanceApi) => {
                        this.openEditDialog(formApi);
                        closeContextToolbar();
                    }).bind(this),
                },
                {
                    type: "contextformbutton",
                    icon: this.removeIcon,
                    text: this.text(this.removeText),
                    tooltip: this.text(this.removeText),
                    primary: false,
                    onAction: (() => {
                        const node = this.getNode();
                        if (node) {
                            node.remove();
                        }
                        closeContextToolbar();
                    }).bind(this),
                },
            ],
        });
    }
}


class Registry {
    static #instance: Registry;

    handles: Map<string, ShortcodeHandle>;

    private constructor() {
        this.handles = new Map<string, ShortcodeHandle>();
    }

    public static get instance(): Registry {
        if (!Registry.#instance) {
            Registry.#instance = new Registry();
        }
        return Registry.#instance;
    }

    public static register(handle: ShortcodeHandle) {
        if (Registry.instance.handles.has(handle.keyword)) {
            throw Error(`Keyword ${handle.keyword} already registered as ${Registry.instance.handles.get(handle.keyword)}`);
        }
        Registry.instance.handles.set(handle.keyword, handle);
    }
    public static unregister(handle: ShortcodeHandle | string): ShortcodeHandle {
        const keyword = handle instanceof ShortcodeHandle ? handle.keyword : handle;
        const old_handle = Registry.instance.handles.get(keyword);
        if (handle instanceof ShortcodeHandle && old_handle !== handle) {
            throw Error(`Keyword ${keyword} registered as a different handle: ${old_handle}`);
        }
        Registry.instance.handles.delete(keyword);
        return old_handle;
    }
    public static unregisterAll() {
        Registry.instance.handles.clear();
    }

    public static setupAll(editor: Editor, parser: Parser) {
        Registry.instance.handles.forEach((value: ShortcodeHandle, key: string) => {
            value.setup(editor);
            parser.register(value.renderPreview.bind(value), key, value.endword);
        });
    }
}


export { ShortcodeHandle, Registry };
