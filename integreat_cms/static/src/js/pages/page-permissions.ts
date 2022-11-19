/**
 * This file contains all event handlers and functions which are needed for granting and revoking permissions on individual pages.
 */
import { createIconsAt } from "../utils/create-icons";
import { getCsrfToken } from "../utils/csrf-token";

// ajax call for updating the page permissions
const updatePagePermission = async (url: string, pageId: string, userId: string, permission: string) => {
    const response = await fetch(url, {
        method: "POST",
        headers: {
            "X-CSRFToken": getCsrfToken(),
        },
        body: JSON.stringify({
            page_id: pageId,
            user_id: userId,
            permission,
        }),
    });

    const HTTP_STATUS_OK = 200;
    if (response.status !== HTTP_STATUS_OK) {
        return "";
    }
    const data = await response.text();

    if (data) {
        // insert response into table
        document.getElementById("page_permission_table").innerHTML = data;
        // set new event listeners
        /* eslint-disable-next-line @typescript-eslint/no-use-before-define */
        setPagePermissionEventListeners();
        // trigger icon replacement
        createIconsAt(document.getElementById("page_permission_table"));
    }

    return "";
};

// function for granting page permissions
const grantPagePermission = async ({ target }: Event) => {
    const button = target as HTMLElement;
    const userId = button.parentNode.querySelector("select").value;
    // only submit ajax request when user is selected
    if (userId) {
        await updatePagePermission(
            button.getAttribute("data-url"),
            button.getAttribute("data-page-id"),
            userId,
            button.getAttribute("data-permission")
        );
    }
};

// function for revoking page permissions
const revokePagePermission = async ({ target }: Event) => {
    const link = (target as HTMLElement).closest("a");
    await updatePagePermission(
        link.getAttribute("href"),
        link.getAttribute("data-page-id"),
        link.getAttribute("data-user-id"),
        link.getAttribute("data-permission")
    );
};

// function to set the page permission event listeners
const setPagePermissionEventListeners = () => {
    document.querySelectorAll(".grant-page-permission").forEach((node) => {
        node.addEventListener("click", (event) => {
            event.preventDefault();
            grantPagePermission(event);
        });
    });
    document.querySelectorAll(".revoke-page-permission").forEach((node) => {
        node.addEventListener("click", (event) => {
            event.preventDefault();
            revokePagePermission(event);
        });
    });
};

document.addEventListener("DOMContentLoaded", setPagePermissionEventListeners);
