export type LinkcheckStats = {
    number_invalid_urls: number;
    number_valid_urls: number;
    number_ignored_urls: number;
    number_unchecked_urls: number;
    number_all_urls: number;
};

/*
 * This function inserts the linkcheck stats into the widget
 */
const loadLinkcheckStats = async (): Promise<void> => {
    // If the page has no table, do nothing
    const linkcheckTable = document.getElementById("linkcheck-stats");
    if (!linkcheckTable) {
        return;
    }

    // Get HTML elements
    const statsNetworkError = document.getElementById("stats-network-error");
    const statsServerError = document.getElementById("stats-server-error");
    const statsLoading = document.getElementById("stats-loading");

    // Hide error in case it was shown before
    statsNetworkError.classList.add("hidden");
    statsServerError.classList.add("hidden");

    // Show loading icon
    statsLoading.classList.remove("hidden");

    // Get AJAX URL
    const url = linkcheckTable.getAttribute("data-linkcheck-stats-url");

    try {
        const response = await fetch(url);

        const HTTP_STATUS_OK = 200;
        if (response.status === HTTP_STATUS_OK) {
            // The response text contains the data from Matomo as JSON.
            const stats = (await response.json()) as LinkcheckStats;
            document.getElementById("number_invalid_urls").textContent = stats.number_invalid_urls.toString();
            document.getElementById("number_valid_urls").textContent = stats.number_valid_urls.toString();
            document.getElementById("number_ignored_urls").textContent = stats.number_ignored_urls.toString();
            document.getElementById("number_unchecked_urls").textContent = stats.number_unchecked_urls.toString();
            document.getElementById("number_all_urls").textContent = stats.number_all_urls.toString();
            // Show table
            linkcheckTable.classList.remove("hidden");
        } else {
            // Server error - CMS server down/malfunctioning
            console.error("Server Error:", response.headers);
            statsServerError.classList.remove("hidden");
        }
    } catch (error) {
        // Network error during fetch
        console.error("Network error during fetch:", error);
        statsNetworkError.classList.remove("hidden");
    } finally {
        // Hide loading icon
        statsLoading.classList.add("hidden");
    }
};

window.addEventListener("load", async () => {
    // Initialize stats data
    await loadLinkcheckStats();
});
