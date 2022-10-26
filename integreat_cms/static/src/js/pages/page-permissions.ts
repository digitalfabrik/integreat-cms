/**
 * This file contains all event handlers and functions which are needed for granting and revoking permissions on individual pages.
 */
import { create_icons_at } from "../utils/create-icons";
import { getCsrfToken } from "../utils/csrf-token";

document.addEventListener("DOMContentLoaded", setPagePermissionEventListeners);

// function to set the page permission event listeners
function setPagePermissionEventListeners() {
    document.querySelectorAll(".grant-page-permission").forEach(function (node) {
        node.addEventListener("click", (event) => {
            event.preventDefault();
            grantPagePermission(event);
        });
    });
    document.querySelectorAll(".revoke-page-permission").forEach(function (node) {
        node.addEventListener("click", (event) => {
            event.preventDefault();
            revokePagePermission(event);
        });
    });
}

// function for granting page permissions
async function grantPagePermission({ target }: Event) {
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
}

// function for revoking page permissions
async function revokePagePermission({ target }: Event) {
    const link = (target as HTMLElement).closest("a");
    await updatePagePermission(
        link.getAttribute("href"),
        link.getAttribute("data-page-id"),
        link.getAttribute("data-user-id"),
        link.getAttribute("data-permission")
    );
}

// ajax call for updating the page permissions
async function updatePagePermission(url: string, pageId: string, userId: string, permission: string) {
    const response = await fetch(url, {
        method: "POST",
        headers: {
            "X-CSRFToken": getCsrfToken(),
        },
        body: JSON.stringify({
            page_id: pageId,
            user_id: userId,
            permission: permission,
        }),
    });

    if (response.status !== 200) {
        return "";
    }
    const data = await response.text();

    if (data) {
        // insert response into table
        document.getElementById("page_permission_table").innerHTML = data;
        // set new event listeners
        setPagePermissionEventListeners();
        // trigger icon replacement
        create_icons_at(document.getElementById("page_permission_table"));
    }
}
