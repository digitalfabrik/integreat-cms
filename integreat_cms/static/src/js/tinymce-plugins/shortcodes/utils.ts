/// <reference path="../tinymce.d.ts" />
import type { ToolbarButtonInstanceApi, ContextFormInstanceApi, ContextFormButtonInstanceApi, ContextFormToggleButtonInstanceApi, DialogInstanceApi, DialogData, MenuItemInstanceApi, DialogSpec, BodyComponentSpec } from "../tinymce.d.ts";
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
 * - number:                   How many positional arguments have to be given (exactly, not more and not less).
 * - [number, number | null]:  How many positional arguments are required, and up to how many CAN be given (Infinity or null means unbounded).
 * - null:                     Allow any number of positional arguments.
 * Keyword arguments:
 * - (string | [string, boolean] | null)[]:  List of all keyword arguments being accepted.
 *                                           If an item is given as a list where the second value is true, the keyword is required.
 *                                           Also serves as a canonical order normalizing the shortcode.
 *                                           If the list contains null, anything is accepted as optional argument.
 * - null:                                   Allow any keyword argument.
 */
type PargsConstraint = number | [number, number | null] | null;
type KWargsDescriptor = (string | [string, boolean] | null)[] | null;


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

    static escape(str: string): string {
        return str.includes(" ") ? `"${str.replace(/"/g, '\\"')}"` : str;
    }

    pargs: PargsConstraint = null;
    kwargs: KWargsDescriptor = null;
    get maxPargs() {
        if (this.pargs === null)
            return Infinity;
        if (typeof this.pargs === "number")
            return this.pargs;
        else if (this.pargs[1] === null)
            return Infinity;
        else
            return this.pargs[1];
    }
    get minPargs() {
        if (this.pargs === null)
            return 0;
        if (typeof this.pargs === "number")
            return this.pargs;
        else
            return this.pargs[0];
    }
    get requiredKWargs(): Set<string> {
        if (this.kwargs === null)  return new Set();
        return new Set(this.kwargs.filter(kw => kw !== null).reduce((acc, key: string | [string, boolean] | null) => {
            if (typeof key === "string") {
                acc.push(key);
            } else if (key !== null && key[1]) {
                acc.push(key[0]);
            }
            return acc;
        }, []));
    }
    get optionalKWargs(): Set<string> {
        if (this.kwargs === null)  return new Set();
        return new Set(this.kwargs.filter(kw => kw !== null).reduce((acc, key: string | [string, boolean] | null) => {
            if (key !== null && !(typeof key === "string") && !key[1]) {
                acc.push(key[0]);
            }
            return acc;
        }, []));
    }
    get acceptingArbitraryKWargs(): boolean {
        if (this.kwargs === null)  return true;
        if (this.kwargs.includes(null))  return true;
        return false;
    }
    lastUnsavedPargs: string[] | null = null;
    lastUnsavedKWargs: [string, string][] | null = null;

    text(text: TextDescriptor): string {
        // A helper method to render a string from either a fixed value or a dynamic function
        if (typeof text === "string") {
            return text;
        }
        return text(this);
    }

    predicate(node: Element): boolean {
        // A method determining whether a node in TinyMCE represents this shortcode
        // (e.g. whether the toolbar specific to this shortcode should be shown)
        if (!("dataset" in node))
            return false;
        const dataset = (node as HTMLElement).dataset;
        return dataset.shortcode && (dataset.shortcode == this.keyword || !this.keyword);
    }

    getNode(): HTMLElement | null {
        // A helper method to get the shortcode node the user has currently selected
        const node = this.editor.selection.getNode();
        return this.predicate(node) ? node : null;
    };

    sortKWargs(kwpairs: Iterable<[string, string]> | [string, string][]): [string, string][] {
        // A helper method determining a canonical order for keyword arguments
        const order = this.kwargs !== null ? this.kwargs.filter(kw => kw !== null).map(kw => typeof kw === "string" ? kw : kw[0]) : [];
        if (!(kwpairs instanceof Array))  kwpairs = Array.from(kwpairs);
        return (kwpairs as Array<[string, string]>).sort((a, b) => {
            const aPos = order.includes(a[0]) ? order.indexOf(a[0]) : order.length;
            const bPos = order.includes(b[0]) ? order.indexOf(b[0]) : order.length;
            return aPos - bPos;
        });
    }

    validate(pargs: string[], kwargs: {[key: string]: string}): boolean {
        if (pargs.length < this.minPargs || pargs.length > this.maxPargs)
            return false;
        // Positional arguments pass!

        if (this.kwargs === null)
            return true;
        const keywords = new Set(Object.keys(kwargs));
        const requiredKWargs = this.requiredKWargs;
        // Check if any required keyword arguments are missing
        if (requiredKWargs.difference(keywords).size > 0)
            return false;
        // Check if there are any keyword arguments that are not allowed
        if (!this.acceptingArbitraryKWargs && keywords.difference(requiredKWargs).difference(this.optionalKWargs).size > 0)
            return false;

        // All arguments pass!
        return true;
    }

    argsFromNode(node: HTMLElement | null): [string[], Map<string, string>] {
        let prefix = "parg";
        const pargs = [...Object.entries(node !== null ? node.dataset : {})].reduce((acc, pair) => {
            if (pair[0].startsWith(prefix)) {
                const index = parseInt(pair[0].slice(prefix.length));
                acc[index] = pair[1];
            }
            return acc;
        }, []);
        while (pargs.length < this.minPargs) {
            pargs.push("");
        }

        prefix = "kw";
        const kwargs = [...Object.entries(node !== null ? node.dataset : {})].reduce((acc, pair) => {
            if (pair[0].startsWith(prefix)) {
                // Revert camelCase transformation automatically done by the dataset api
                let keyword = pair[0].replace(/[A-Z]/g, c => `-${c.toLowerCase()}`);
                // Strip the prefix + dash
                keyword = keyword.slice(prefix.length + 1);
                acc.push([keyword, pair[1]]);
            }
            return acc;
        }, []);

        return [pargs, new Map(kwargs)];
    }

    truncateArgs(pargs: string[], kwargs: Map<string, string>): [string[], Map<string, string>] {
        // Ensure the arguments fit the specification
        let newPargs = [...pargs];
        const newKWargs = new Map(kwargs);

        // Ensure the correct number of positional arguments
        if (newPargs.length > this.maxPargs) {
            newPargs = newPargs.slice(0, this.maxPargs);
        }
        while (newPargs.length < this.minPargs) {
            newPargs.push("");
        }

        // Ensure all required keywords exist
        const requiredKWargs = this.requiredKWargs;
        const optionalKWargs = this.optionalKWargs;
        requiredKWargs.forEach(kwarg => {
            if (!newKWargs.has(kwarg)) {
                newKWargs.set(kwarg, "");
            }
        });
        if (!this.acceptingArbitraryKWargs) {
            // Ensure no unallowed keywords exist
            kwargs.forEach((v, kwarg) => {
                if (!(requiredKWargs.has(kwarg) || optionalKWargs.has(kwarg))) {
                    newKWargs.delete(kwarg);
                }
            });
        }

        console.log(`truncateArgs() →`, newKWargs);
        return [newPargs, newKWargs];
    }

    renderShortcode(pargs: string[], kwargs: Map<string, string>): string {
        // The canonical text representation of the shortcode
        const pairs = this.sortKWargs(kwargs.entries()).map(pair => pair.map(ShortcodeHandle.escape).join("="));
        const parts = [ShortcodeHandle.escape(this.keyword), ...pargs.map(ShortcodeHandle.escape), ...pairs];
        return `[${parts.join(" ")}]`;
    }

    renderPreviewNode(pargs: string[], kwargs: Map<string, string>): string {
        // The html string representation of the shortcode in the TinyMCE editor
        console.log(`renderPreviewNode()`, pargs, kwargs);
        const ppairs = pargs.map((arg, i) => `data-parg${i}="${arg}"`);
        const kwpairs = this.sortKWargs(kwargs.entries()).map(([key, value]) => `data-kw-${key}=${ShortcodeHandle.escape(value)}`);
        const parts = [`class="mceNonEditable"`, `data-shortcode="${this.keyword}"`, ...ppairs, ...kwpairs];
        return `<span ${parts.join(" ")}>${this.renderPreview(pargs, kwargs)}</span>`;
    }

    renderPreview(pargs: string[], kwargs: Map<string, string>): string {
        // The html string representation of the shortcode preview in the TinyMCE editor
        // By default this is just the canonical text representation. This function will be overwritten by most subclasses.
        return this.renderShortcode(pargs, kwargs);
    }

    reconstructArgsFromDialog(api: DialogInstanceApi<DialogData>): [string[], {[key: string]: string}, [string, string][]] {
        // Reconstruct the positional and keyword arguments from the form data
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
        type OrderedPairs = [string, string][];
        const orderedKWargs: OrderedPairs = [];
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
                        // Normalize keys to dash-style
                        // This is not its own overridable function because it is already automatically transformed
                        // to dash-style on the marker node representing the shortode to TinyMCE (this is how HTML attributes work)
                        // and to camelCase by the dataset API on JS side.
                        key = key.toLowerCase().replace(/\s+/g, "-");
                        acc[key] = value;
                        orderedKWargs[id] = [key, value];
                        delete acc[id];
                    }
                }
            }
            return acc;
        }, {}) as unknown as FinalizedPairs;
        return [pargs, kwargs, orderedKWargs];
    }

    openEditDialog() {
        const node = this.getNode();
        const [initialPargs, initialKWargs] = this.truncateArgs(...this.argsFromNode(node));
        this.lastUnsavedPargs = initialPargs;
        this.lastUnsavedKWargs = this.sortKWargs(initialKWargs.entries());
        return this.displayEditDialog(initialPargs, this.lastUnsavedKWargs);
    }

    displayEditDialog(initialPargs: string[], initialKWargs: [string, string][]) {
        // The default implementation for constructing the edit dialog for a generic shortcode
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
                type: "htmlpanel",
                html: `<div class="tox-bar tox-form__controls-h-stack">
                    <div class="tox-form__group">
                        <button id="parg-remove" type="button" title="Remove positional argument" tabindex="-1" data-alloy-tabstop="true" class="tox-button tox-button--secondary">-</button>
                    </div>
                    <div class="tox-form__group">
                        <button id="parg-add" type="button" title="Add positional argument" tabindex="-1" data-alloy-tabstop="true" class="tox-button tox-button--secondary">+</button>
                    </div>
                </div>`,
                /*type: "bar",
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
                ],*/
            });
        }
        initialKWargs.forEach(([keyword, value]: [string, string], i: number) => {
            if (this.acceptingArbitraryKWargs) {
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
        if (this.acceptingArbitraryKWargs) {
            argumentItems.push({
                type: "bar",
                items: [
                    {
                        type: "htmlpanel",
                        html: `<div class="tox-bar tox-form__controls-h-stack">
                            <div class="tox-form__group">
                                <button id="kwarg-remove" type="button" title="Remove keyword argument" tabindex="-1" data-alloy-tabstop="true" class="tox-button tox-button--secondary">-</button>
                            </div>
                            <div class="tox-form__group">
                                <button id="kwarg-add" type="button" title="Add keyword argument" tabindex="-1" data-alloy-tabstop="true" class="tox-button tox-button--secondary">+</button>
                            </div>
                        </div>`,
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
                const [pargs, kwargs, orderedKWargs] = this.reconstructArgsFromDialog(api);
                this.lastUnsavedPargs = pargs;
                this.lastUnsavedKWargs = orderedKWargs;

                // Don't close the dialog if the arguments are not valid
                if (!this.validate(pargs, kwargs))
                    return;

                api.close();
                this.lastUnsavedPargs = null;
                this.lastUnsavedKWargs = null;

                // Either insert a new shortcode or update the existing one
                const node = this.getNode();
                if (!node) {
                    this.editor.insertContent(this.renderShortcode(pargs, new Map(Object.entries(kwargs))));
                } else {
                    node.remove();
                    this.editor.insertContent(this.renderShortcode(pargs, new Map(Object.entries(kwargs))));
                }
            },
            onChange: (api: DialogInstanceApi<DialogData>) => {
                const [pargs, kwargs, orderedKWargs] = this.reconstructArgsFromDialog(api);
                this.lastUnsavedPargs = pargs;
                this.lastUnsavedKWargs = orderedKWargs;
            },
        };
        console.log(`[${this.keyword}]`, this, dialogConfig);

        setTimeout(() => {
            const dialog = document.querySelector('.tox-dialog');
            const pargRemove = dialog.querySelector('#parg-remove');
            const pargAdd    = dialog.querySelector('#parg-add');
            if (pargRemove) {
                pargRemove.addEventListener("click", (() => {
                    if (this.lastUnsavedPargs === null || this.lastUnsavedPargs.length <= this.minPargs)
                        return;
                    this.lastUnsavedPargs.pop();
                    this.editor.windowManager.close();
                    this.displayEditDialog(this.lastUnsavedPargs, this.lastUnsavedKWargs);
                }).bind(this));
            }
            if (pargAdd) {
                pargAdd.addEventListener("click", (() => {
                    if (this.lastUnsavedPargs === null || this.lastUnsavedPargs.length >= this.maxPargs)
                        return;
                    this.lastUnsavedPargs.push("");
                    this.editor.windowManager.close();
                    this.displayEditDialog(this.lastUnsavedPargs, this.lastUnsavedKWargs);
                }).bind(this));
            }
            const kwargRemove = dialog.querySelector('#kwarg-remove');
            const kwargAdd    = dialog.querySelector('#kwarg-add');
            if (kwargRemove) {
                kwargRemove.addEventListener("click", (() => {
                    console.log(`kwargRemove() this.lastUnsavedKWargs === null ? ${this.lastUnsavedKWargs === null}`);
                    if (this.lastUnsavedKWargs === null)
                        return;
                    const requiredKWargs = this.requiredKWargs;
                    // Throw away the last keyword that is not required
                    for (let i = this.lastUnsavedKWargs.length-1; i >= 0; i--) {
                        if (requiredKWargs.has(this.lastUnsavedKWargs[i][0]))
                            continue;
                        const beforeThis = this.lastUnsavedKWargs.slice(0, i);
                        const afterThis = this.lastUnsavedKWargs.slice(i+1, this.lastUnsavedKWargs.length);
                        this.lastUnsavedKWargs = beforeThis.concat(afterThis);
                        break;
                    };
                    this.editor.windowManager.close();
                    this.displayEditDialog(this.lastUnsavedPargs, this.lastUnsavedKWargs);
                }).bind(this));
            }
            if (kwargAdd) {
                kwargAdd.addEventListener("click", (() => {
                    console.log(`kwargAdd() this.lastUnsavedKWargs === null ? ${this.lastUnsavedKWargs === null}`);
                    if (this.lastUnsavedKWargs === null)
                        return;
                    // A flat list of known keywords in canonical order
                    const order = this.kwargs === null ? [] : this.kwargs.filter(kw => kw !== null).map(([key, required]) => key);
                    function index(x: string): number {
                        // Determine the canonical position of the keyword
                        const i = order.indexOf(x);
                        if (i == -1) return Infinity; // If the keyword is unknown, sort it last
                        return i;
                    }
                    const requiredKWargs = this.requiredKWargs;
                    const keys = new Set(this.lastUnsavedKWargs.map(([key, value]) => key));
                    const missingRequired = requiredKWargs.difference(keys);
                    let key;
                    if (missingRequired.size > 0) {
                        // Somehow, required keywords are missing. Add the first one by canonical order
                        key = Array.from(missingRequired).sort((a, b) => index(a) - index(b)).reverse()[0];
                    } else {
                        const optionalKWargs = this.optionalKWargs;
                        const missingOptional = optionalKWargs.difference(keys);
                        if (missingOptional.size > 0) {
                            // Add the first known optional argument by canonical order. If we don't know any and we accept arbitrary arguments, leave the key empty
                            key = Array.from(missingOptional).sort((a, b) => index(a) - index(b)).reverse()[0] || "";
                        } else if (this.acceptingArbitraryKWargs)
                            key = "";
                        else
                            return; // There are no arguments left to add, stop without doing anything
                    }
                    // Finally, actually append the key value pair and retrigger the dialog
                    this.lastUnsavedKWargs.push([key, ""]);
                    this.editor.windowManager.close();
                    this.displayEditDialog(this.lastUnsavedPargs, this.lastUnsavedKWargs);
                }).bind(this));
            }
        }, 0);

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

        editor.ui.registry.addButton(`edit_shortcode_${this.keyword}`, {
            text: this.text(this.editText),
            tooltip: this.text(this.editText),
            icon: this.editIcon,
            onAction: ((api: ToolbarButtonInstanceApi) => {
                this.openEditDialog();
                closeContextToolbar();
            }).bind(this),
        });

        editor.ui.registry.addButton(`remove_shortcode_${this.keyword}`, {
            text: this.text(this.removeText),
            tooltip: this.text(this.removeText),
            icon: this.removeIcon,
            onAction: (() => {
                const node = this.getNode();
                if (node) {
                    node.remove();
                }
                closeContextToolbar();
            }).bind(this),
        });

        // This form opens when a shortcode is currently selected with the cursor
        editor.ui.registry.addContextToolbar(`shortcode_${this.keyword}_context_form`, {
            predicate: this.predicate.bind(this),
            position: "node",
            scope: "node",
            items: `edit_shortcode_${this.keyword} remove_shortcode_${this.keyword}`,
        });
    }
}


class Registry {
    static #instance: Registry;

    handles: Map<string, ShortcodeHandle>;
    unknownHandleFactory: null | ((keyword: string) => ShortcodeHandle);

    private constructor() {
        this.handles = new Map<string, ShortcodeHandle>();
        this.unknownHandleFactory = null;
    }

    public static get instance(): Registry {
        if (!Registry.#instance) {
            Registry.#instance = new Registry();
        }
        return Registry.#instance;
    }

    public static has(keyword: string): boolean {
        return Registry.instance.handles.has(keyword);
    }

    public static get(keyword: string): ShortcodeHandle | null {
        return Registry.instance.handles.get(keyword);
    }

    public static register(handle: ShortcodeHandle) {
        if (Registry.has(handle.keyword)) {
            throw Error(`Keyword ${handle.keyword} already registered as ${Registry.get(handle.keyword)}`);
        }
        Registry.instance.handles.set(handle.keyword, handle);
    }
    public static unregister(handle: ShortcodeHandle | string): ShortcodeHandle {
        const keyword = handle instanceof ShortcodeHandle ? handle.keyword : handle;
        const old_handle = Registry.get(keyword);
        if (handle instanceof ShortcodeHandle && old_handle !== handle) {
            throw Error(`Keyword ${keyword} registered as a different handle: ${old_handle}`);
        }
        Registry.instance.handles.delete(keyword);
        return old_handle;
    }
    public static unregisterAll() {
        Registry.instance.handles.clear();
    }

    public static setUnknownHandleFactory(factory: (keyword: string) => ShortcodeHandle) {
        this.instance.unknownHandleFactory = factory;
    }

    public static setupAll(editor: Editor, parser: Parser) {
        Registry.instance.handles.forEach((value: ShortcodeHandle, key: string) => {
            value.setup(editor);
            parser.register(value.renderPreviewNode.bind(value), key, value.endword);
        });
        if (this.instance.unknownHandleFactory !== null) {
            parser.setUnknownHandlerFactory((keyword: string) => {
                const handle = this.instance.unknownHandleFactory(keyword);
                const fn = handle.renderPreviewNode.bind(handle);
                Registry.register(handle);
                handle.setup(editor);
                parser.register(fn, keyword);
                console.log(`created and registered dummy handler for ${keyword}`);
                return fn;
            });
        } else {
            parser.setUnknownHandlerFactory(null);
        }
    }
}


export { ShortcodeHandle, Registry };
