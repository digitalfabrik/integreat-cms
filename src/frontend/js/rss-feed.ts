/**
 * This file contains all functions which are needed for the RSS feed
 */

// Load RSS feed initially
window.addEventListener("load", () => loadRssFeed());


async function loadRssFeed() {
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
    const controller = new AbortController();
    const timeoutId = setTimeout(() => {
      controller.abort();
      handleError();
    }, 5000);

    fetch(url, {signal: controller.signal})
      .then((response: Response) => {
        if (response.ok && response.status === 200) {
          return response.text();
        } 
        throw new Error("Error during fetching of RSS feed");
      }).then((rawFeed: string) => {
        feedLoading.classList.add("hidden");
        clearTimeout(timeoutId);
        let parser = new DOMParser;
        let feedHtml = parser.parseFromString(rawFeed, "text/xml");
        console.log(feedHtml);

        let firstEntry = 0, lastEntry = 3; 
        feedWidget.innerHTML += loadRssEntries(feedHtml, firstEntry, lastEntry);
        const readMoreButton = document.getElementById("read-more")
        readMoreButton.classList.remove("hidden");
        readMoreButton.addEventListener("click", () => {
          
          firstEntry = lastEntry;
          lastEntry += 3;

          feedWidget.innerHTML += loadRssEntries(feedHtml, firstEntry, lastEntry);

          if (feedHtml.querySelectorAll("item").length - 1 <= firstEntry) {
            readMoreButton.classList.add("hidden");

            let entries = document.querySelectorAll(".rss-entry");
            entries[entries.length - 1].classList.remove("border-b")
            entries[entries.length - 1].classList.remove("border-gray-400")
            entries[entries.length - 1].classList.remove("mb-2");
          }     
        }); 
    }).catch ((err) => {
      // console.error(err);
      handleError();
    });
  }
}


function loadRssEntries(doc: Document, firstEntry: number, lastEntry: number) : String {
  let feed = "";

  Array.from(doc.querySelectorAll("item")).slice(firstEntry, lastEntry).forEach((node) => {
    let link:String = node.querySelector("link").innerHTML;
    let title:string = node.querySelector("title").innerHTML;
    let content:String = node.querySelector("description").textContent;
    if (title && link && content) {
      let rssEntry = '<div class="rss-entry pb-2 border-b border-gray-400 mb-2">'
        + '<a href="' 
        + link 
        + '" target="_blank" rel="noopener noreferrer" class="block py-b font-bold text-blue-500 hover:text-blue-700">'
        + title 
        + '</a>' + '<div class="text-gray-600 py-2"></div>'
        + '<p class="pb-1">' + content
        + '</div>'

      feed += rssEntry;
    }
  }); 
  return feed;
}
