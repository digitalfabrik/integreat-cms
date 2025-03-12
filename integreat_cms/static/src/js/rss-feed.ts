/**
 * This file contains all functions which are needed for the RSS feed
 */

const checkIfShouldBeIncluded = (node: any): boolean => {
    let shouldBeIncluded = false;
    const categories: NodeListOf<HTMLLinkElement> = node.querySelectorAll("category");
    categories.forEach((category) => {
        if (category.innerHTML.includes("Redaktionssystem")) {
            shouldBeIncluded = true;
        }
    });
    return shouldBeIncluded;
};

const loadRssEntries = (doc: Document, lastEntry: number): string => {
    let feed = "";
    let selectedElements = 0;

    Array.from(doc.querySelectorAll("item")).forEach((node) => {
        const shouldBeIncluded = checkIfShouldBeIncluded(node);
        const link: string = node.querySelector("link").innerHTML;
        const title: string = node.querySelector("title").innerHTML;
        const content: string = node.querySelector("description").textContent;
        if (shouldBeIncluded && title && link && content) {
            selectedElements += 1;
            if (selectedElements <= lastEntry) {
                const rssEntry =
                    `<div class="rss-entry pb-2 border-b border-gray-400 mb-2">` +
                    `<a href="${link}" target="_blank" rel="noopener noreferrer" class="block py-b font-bold text-blue-500 hover:text-blue-700">${title}</a>` +
                    `<div class="text-gray-600 py-2"></div>` +
                    `<p class="pb-1">${content}</div>`;
                feed += rssEntry;
            }
        }
    });
    return feed;
};

const loadRssFeed = async () => {
    const feedWidget = document.querySelector(".rss-feed");

    if (feedWidget) {
        const feedLoading = document.getElementById("feed-loading");
        const reloadButton = document.getElementById("reload");

        const handleError = () => {
            feedLoading.classList.add("hidden");
            reloadButton.classList.remove("hidden");
            reloadButton.addEventListener("click", loadRssFeed);
        };

        feedLoading.classList.remove("hidden");
        reloadButton.classList.add("hidden");
        const url = feedWidget.attributes[1].value;

        // set timeout
        const timeoutDuration = 5000;
        const controller = new AbortController();
        const timeoutId = setTimeout(() => {
            controller.abort();
            handleError();
        }, timeoutDuration);

        const entriesStepSize = 3;

        fetch(url, { signal: controller.signal })
            .then((response: Response) => {
                const HTTP_STATUS_OK = 200;
                if (response.ok && response.status === HTTP_STATUS_OK) {
                    return response.text();
                }
                throw new Error("Error during fetching of RSS feed");
            })
            .then((rawFeed: string) => {
                feedLoading.classList.add("hidden");
                clearTimeout(timeoutId);
                const parser = new DOMParser();
                const feedHtml = parser.parseFromString(rawFeed, "text/xml");
                console.debug("The parsed feed html:", feedHtml);

                let firstEntry = 0;
                let lastEntry = entriesStepSize;
                feedWidget.innerHTML += loadRssEntries(feedHtml, lastEntry);
                const readMoreButton = document.getElementById("read-more");
                readMoreButton.classList.remove("hidden");
                readMoreButton.addEventListener("click", () => {
                    firstEntry = lastEntry;
                    lastEntry += entriesStepSize;

                    feedWidget.innerHTML += loadRssEntries(feedHtml, lastEntry);

                    if (feedHtml.querySelectorAll("item").length - 1 <= firstEntry) {
                        readMoreButton.classList.add("hidden");

                        const entries = document.querySelectorAll(".rss-entry");
                        entries[entries.length - 1].classList.remove("border-b");
                        entries[entries.length - 1].classList.remove("border-gray-400");
                        entries[entries.length - 1].classList.remove("mb-2");
                    }
                });
            })
            .catch((_) => {
                handleError();
            });
    }
};

// Load RSS feed initially
window.addEventListener("load", () => loadRssFeed());
