const renderLanguageTabs = () => {
    const globeElement = document.getElementById("language-switcher-globe");
    const textElement = document.getElementById("language-switcher-text");
    const tabWrapper = document.getElementById("tab-wrapper");
    const languageSwitcher = document.getElementById("language-switcher");
    const languageSwitcherListElement = document.getElementById("language-switcher").parentElement;
    const languageSwitcherList = document.getElementById("language-switcher-list");
    const anchorClassesWhenShown = [
        "px-4",
        "py-[calc(0.75rem+2px)]",
        "bg-water-500",
        "rounded-t",
        "hover:bg-white",
        "hover:text-blue-500",
    ];
    const anchorClassesWhenHidden = ["px-3", "py-2", "bg-white", "whitespace-nowrap", "hover:bg-water-500"];

    globeElement?.classList.add("hidden");
    textElement?.classList.remove("hidden");

    if (tabWrapper) {
        const buffer = 20;
        const paddingInWrapper =
            parseFloat(window.getComputedStyle(tabWrapper).paddingLeft) +
            parseFloat(window.getComputedStyle(tabWrapper).paddingRight);
        const availableWidth = tabWrapper.offsetWidth - paddingInWrapper - languageSwitcherListElement.offsetWidth;
        const tabs = Array.from(tabWrapper.children).concat(Array.from(languageSwitcherList.children));

        let usedSpace = 0;
        let tabCount = 0;

        tabs.forEach((tab) => {
            const marginOfTab = parseFloat(window.getComputedStyle(tab).marginRight);
            const anchor = tab.getElementsByTagName("a")[0];
            const fitsWithLanguageSwitcher =
                usedSpace + (tab as HTMLElement).offsetWidth + marginOfTab + buffer <= availableWidth;

            if (!fitsWithLanguageSwitcher && tab !== languageSwitcherListElement && tabCount > 0) {
                tab.classList.remove("mr-2");
                if (anchor) {
                    anchor.classList.remove(...anchorClassesWhenShown);
                    anchor.classList.add(...anchorClassesWhenHidden);
                }
                languageSwitcherList.append(tab);
            } else {
                tab.classList.add("mr-2");
                if (anchor) {
                    if (anchor.closest("#language-switcher-list") === null) {
                        anchor.classList.remove(...anchorClassesWhenHidden);
                        anchor.classList.add(...anchorClassesWhenShown);
                    }
                }
                if (!Array.from(tabWrapper.children).includes(tab)) {
                    tabWrapper.insertBefore(tab, languageSwitcherListElement);
                }
                usedSpace += tab.clientWidth + marginOfTab;
                tabCount += 1;
            }
        });

        const widthOfExtendedButton = languageSwitcher.clientWidth;
        const paddings: number = parseFloat(
            window.getComputedStyle(tabWrapper).paddingLeft + window.getComputedStyle(tabWrapper).paddingRight
        );
        const widthOfFirstTab = tabs[0].clientWidth;
        const minimumNeededSpaceForVerboseButton = widthOfFirstTab + widthOfExtendedButton + paddings + buffer;

        if (minimumNeededSpaceForVerboseButton > tabWrapper.clientWidth) {
            globeElement.classList.remove("hidden");
            textElement.classList.add("hidden");
        }

        if (tabCount === tabs.length) {
            languageSwitcherListElement.classList.add("hidden");
        } else {
            languageSwitcherListElement.classList.remove("hidden");
        }

        const lastTab = languageSwitcherList.lastElementChild;
        if (lastTab) {
            lastTab.getElementsByTagName("a")[0].classList.add("border-b");
        }
    }
};

window.addEventListener("load", () => {
    renderLanguageTabs();
    window.addEventListener("resize", renderLanguageTabs);
});
