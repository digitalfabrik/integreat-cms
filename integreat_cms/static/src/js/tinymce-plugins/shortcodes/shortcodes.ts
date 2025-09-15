/*******************************************
 * JS version of pythons shortcode package *
 * which is licensed under MIT             *
 *******************************************/


// Globally-registered handler functions indexed by keyword.
const global_keywords = new Map<string, [(pargs: string[], kwargs: Map<string, string>, context: any, content?: string) => string, string]>();


// The set of all end-words for globally-registered block-scoped shortcodes.
const global_endwords = new Set<string>();


// Decorator function for globally registering shortcode handlers.
function register(keyword: string, endword: string) {

    function register_function(func: (pargs: string[], kwargs: Map<string, string>, context: any, content?: string) => string) {
        global_keywords.set(keyword, [func, endword]);
        if (endword) {
            global_endwords.add(endword);
        }
        return func;
    }

    return register_function;
}


/***********************
 *  Exception Classes  *
 ***********************/


// Base class for all exceptions raised by the library.
class ShortcodeError extends Error {
    constructor(message: string) {
        super(message);
        this.name = "ShortcodeError";
    }
}


// Raised if the parser detects invalid shortcode syntax.
class ShortcodeSyntaxError extends ShortcodeError {
    constructor(message: string) {
        super(message);
        this.name = "ShortcodeSyntaxError";
    }
}


// Raised if a handler function throws an error.
class ShortcodeRenderingError extends ShortcodeError {
    constructor(message: string) {
        super(message);
        this.name = "ShortcodeRenderingError";
    }
}


/***************
 *  AST Nodes  *
 ***************/


// Input text is parsed into a tree of ASTNode instances.
class ASTNode {
    children: ASTNode[] = [];
    token: Token;

    constructor() {
    }

    render(context: any): string {
        return this.children.map(c => c.render(context)).join("");
    }
}


// Represents ordinary text not enclosed in tag delimiters.
class Text extends ASTNode {
    text: string;

    constructor(text: string) {
        super();
        this.text = text;
    }

    render(context: any): string {
        return this.text;
    }
}


// Base class for atomic and block-scoped shortcodes.
class Shortcode extends ASTNode {
    // Regex for parsing the shortcode's arguments.
    re_args = new RegExp(`
        (?:([^\s'"=]+)=)?
        (
            "((?:[^\\"]|\\.)*)"
            |
            '((?:[^\\']|\\.)*)'
        )
        |
        ([^\s'"=]+)=(\S+)
        |
        (\S+)
    `, "g");

    handler: (pargs: string[], kwargs: Map<string, string>, context: any, content?: string) => string;
    pargs: string[];
    kwargs: Map<string, string>;
    children: ASTNode[];

    constructor(token: Token, handler_function: (pargs: string[], kwargs: Map<string, string>, context: any, content?: string) => string) {
        super();
        this.token = token;
        this.handler = handler_function;
        [this.pargs, this.kwargs] = this.parse_args(token.text.slice(token.keyword.length));
        this.children = [];
    }

    parse_args(argstring: string): [string[], Map<string, string>] {
        const pargs: string[] = [];
        const kwargs = new Map<string, string>();
        for (const match of argstring.matchAll(this.re_args)) {
            if (match.groups[2] || match.groups[5]) {
                const key = match.groups[1] || match.groups[5];
                const value = match.groups[3] || match.groups[4] || match.groups[6];
                if (key) {
                    kwargs.set(key, value);
                } else {
                    pargs.push(value);
                }
            } else {
                pargs.push(match.groups[7]);
            }
        }
        return [pargs, kwargs];
    }
}


// An atomic shortcode is a shortcode with no closing tag.
class AtomicShortcode extends Shortcode {
    /* If the shortcode handler raises an exception we intercept it and wrap it
     * in a ShortcodeRenderingError.
     */
    render(context: any) {
        try {
            return this.handler(this.pargs, this.kwargs, context).toString();
        } catch (ex: unknown) {
            const msg = `An exception was raised while rendering the '${this.token.keyword}' shortcode in line ${this.token.line_number}.`;
            const error = new ShortcodeRenderingError(msg);
            if (ex instanceof Error) {
                error.stack = ex.stack;
            }
            throw error;
        }
    }
}


// A block-scoped shortcode is a shortcode with a closing tag.
class BlockShortcode extends Shortcode {
    /* If the shortcode handler raises an exception we intercept it and wrap it
     * in a ShortcodeRenderingError. The original exception will still be
     * available via the exception's __cause__ attribute.
     */
    render(context: any) {
        const content = this.children.map(c => c.render(context)).join("");
        try {
            return this.handler(this.pargs, this.kwargs, context, content).toString();
        } catch (ex: unknown) {
            const msg = `An exception was raised while rendering the '${this.token.keyword}' shortcode in line ${this.token.line_number}.`
            const error = new ShortcodeRenderingError(msg);
            if (ex instanceof Error) {
                error.stack = ex.stack;
            }
            throw error;
        }
    }
}


/************
 *  Parser  *
 ************/


/* A Parser instance parses input text and renders shortcodes. A single Parser
 * instance can parse an unlimited number of input strings. Note that the parse()
 * method accepts an optional arbitrary context object which it passes on to each
 * shortcode's handler function.
 *
 * If the `inherit_globals` parameter is true, the parser will inherit a copy of
 * the set of globally-registered shortcodes at the moment of instantiation.
 *
 * If `ignore_unknown` is true, unknown shortcodes are ignored. If this parameter
 * is false (the default), unknown shortcodes cause an error.
 */
class Parser {
    start: string;
    end: string;
    esc_start: string;
    keywords: Map<string, [(pargs: string[], kwargs: Map<string, string>, context: any, content?: string) => string, string]>;
    endwords: Set<string>;
    ignore_unknown: boolean;

    constructor(start: string = '[%', end: string = '%]', esc: string = '\\', inherit_globals: boolean = true, ignore_unknown: boolean = false) {
        this.start = start;
        this.end = end;
        this.esc_start = esc + start;
        this.keywords = new Map<string, [(pargs: string[], kwargs: Map<string, string>, context: any, content?: string) => string, string]>(inherit_globals ? global_keywords : null);
        this.endwords = new Set<string>(inherit_globals ? global_endwords : null);
        this.ignore_unknown = ignore_unknown;
    }

    register(func: (pargs: string[], kwargs: Map<string, string>, context: any, content?: string) => string, keyword: string, endword: string = null) {
        this.keywords.set(keyword, [func, endword]);
        if (endword) {
            this.endwords.add(endword);
        }
    }

    parse(text: string, context: any = null) {
        if (!text.includes(this.start)) {
            return text;
        }

        const stack = [new ASTNode()];
        const expecting = [];

        const lexer = new Lexer(text, this.start, this.end, this.esc_start);
        for (const token of lexer.tokenize()) {
            if (token.type == "TEXT") {
                stack[stack.length-1].children.push(new Text(token.text));
            } else if (this.keywords.has(token.keyword)) {
                const [handler, endword] = this.keywords.get(token.keyword);
                if (endword) {
                    const node = new BlockShortcode(token, handler);
                    stack[stack.length-1].children.push(node);
                    stack.push(node);
                    expecting.push(endword);
                } else {
                    const node = new AtomicShortcode(token, handler);
                    stack[stack.length-1].children.push(node);
                }
            } else if (this.endwords.has(token.keyword)) {
                if (expecting.length == 0) {
                    const msg = `Unexpected '${token.keyword}' tag in line ${token.line_number}.`;
                    throw new ShortcodeSyntaxError(msg);
                } else if (token.keyword == expecting[expecting.length-1]) {
                    stack.pop();
                    expecting.pop();
                } else {
                    const msg = `Unexpected '${token.keyword}' tag in line ${token.line_number}. The shortcode parser was expecting a closing '${expecting[-1]}' tag.`;
                    throw new ShortcodeSyntaxError(msg);
                }
            } else if (token.keyword == '') {
                const msg = `Empty shortcode tag in line ${token.line_number}.`;
                throw new ShortcodeSyntaxError(msg);
            } else if (this.ignore_unknown) {
                stack[stack.length-1].children.push(new Text(token.raw_text));
            } else {
                const msg = `Unrecognised shortcode tag '${token.keyword}' in line ${token.line_number}.`
                throw new ShortcodeSyntaxError(msg);
            }
        }

        if (expecting.length) {
            const token = stack[stack.length-1].token;
            const msg = `Unexpected end of document. The shortcode parser was expecting a closing '${expecting[-1]}' tag to close the '${token.keyword}' tag opened in line ${token.line_number}.`;
            throw new ShortcodeSyntaxError(msg);
        }

        return stack.pop().render(context);
    }
}


/***********
 *  Lexer  *
 ***********/


class Token {
    keyword: string;
    type: string;
    text: string;
    raw_text: string;
    line_number: number;

    constructor(token_type: string, token_text: string, raw_text: string, line_number: number) {
        const words = token_text.split(/\s+/);
        this.keyword = words ? words[0] : '';
        this.type = token_type;
        this.text = token_text;
        this.raw_text = raw_text;
        this.line_number = line_number;
    }

    toString(): string {
        return `(${this.type}, ${this.text.toString()}, ${this.line_number})`;
    }
}


class Lexer {
    text: string;
    start: string;
    end: string;
    esc_start: string;
    tokens: Token[];
    index: number;
    line_number: number;

    constructor(text: string, start: string, end: string, esc_start: string) {
        this.text = text;
        this.start = start;
        this.end = end;
        this.esc_start = esc_start;
        this.tokens = [];
        this.index = 0;
        this.line_number = 1;
    }

    match(target: string): boolean {
        if (this.text.startsWith(target, this.index)) {
            return true;
        }
        return false;
    }

    advance() {
        if (this.text[this.index] == '\n') {
            this.line_number += 1;
        }
        this.index += 1;
    }

    tokenize(): Token[] {
        while (this.index < this.text.length) {
            if (this.match(this.esc_start)) {
                this.read_escaped_tag_delimiter();
            } else if (this.match(this.start)) {
                this.read_tag();
            } else {
                this.read_text();
            }
        }
        return this.tokens;
    }

    read_escaped_tag_delimiter() {
        this.index += this.esc_start.length;
        this.tokens.push(new Token("TEXT", this.start, this.esc_start, this.line_number));
    }

    read_tag() {
        this.index += this.start.length;
        const start_index = this.index;
        const start_line_number = this.line_number;
        while (this.index < this.text.length) {
            if (this.match(this.end)) {
                const text = this.text.slice(start_index, this.index).trim();
                const raw_text = this.text.slice(start_index-this.start.length, this.index+this.end.length);
                this.tokens.push(new Token("TAG", text, raw_text, start_line_number));
                this.index += this.end.length;
                return;
            }
            this.advance();
        }
        const msg = `Unclosed shortcode tag. The tag was opened in line ${start_line_number}.`;
        throw new ShortcodeSyntaxError(msg);
    }

    read_text() {
        const start_index = this.index;
        const start_line_number = this.line_number;
        while (this.index < this.text.length) {
            if (this.match(this.esc_start) || this.match(this.start)) {
                break;
            }
            this.advance();
        }
        const text = this.text.slice(start_index, this.index);
        this.tokens.push(new Token("TEXT", text, text, start_line_number));
    }
}


export { register, ShortcodeError, ShortcodeSyntaxError, ShortcodeRenderingError, ASTNode, Text, Shortcode, AtomicShortcode, BlockShortcode, Parser, Token, Lexer };
