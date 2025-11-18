import * as preact from "preact";

/**
 * See https://github.com/preactjs/preact-router/issues/475
 */

declare module "preact-router" {
    export function Link(props: preact.JSX.AnchorHTMLAttributes<HTMLAnchorElement>): preact.VNode;
}

declare module "preact-router/match" {
    export function Link(props: preact.JSX.AnchorHTMLAttributes<HTMLAnchorElement>): preact.VNode;
}
