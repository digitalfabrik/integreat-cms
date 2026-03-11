const BUFFER = 20;

const hideElement = (element: HTMLElement | null) => {
    element?.classList.add("hidden");
};

const showElement = (element: HTMLElement | null) => {
    element?.classList.remove("hidden");
};

const calculateAvailableWidth = (tabWrapper: HTMLElement, languageSwitcherListElement: HTMLElement): number => {
    const paddingInWrapper =
        parseFloat(window.getComputedStyle(tabWrapper).paddingLeft) +
        parseFloat(window.getComputedStyle(tabWrapper).paddingRight);
    return tabWrapper.offsetWidth - paddingInWrapper - languageSwitcherListElement.offsetWidth;
};

const getTabMargin = (tab: Element): number => parseFloat(window.getComputedStyle(tab).marginRight);

const fitsInAvailableWidth = (tab: Element, usedSpace: number, availableWidth: number): boolean => {
    const marginOfTab = getTabMargin(tab);
    return usedSpace + (tab as HTMLElement).offsetWidth + marginOfTab + BUFFER <= availableWidth;
};

const moveToLanguageSwitcherList = (tab: Element, languageSwitcherList: HTMLElement) => {
    languageSwitcherList.append(tab);
};

const moveToTabWrapper = (tab: Element, tabWrapper: HTMLElement, languageSwitcherListElement: HTMLElement) => {
    if (!Array.from(tabWrapper.children).includes(tab)) {
        tabWrapper.insertBefore(tab, languageSwitcherListElement);
    }
};

const isButtonTooWide = (firstTab: Element, languageSwitcher: HTMLElement, tabWrapper: HTMLElement): boolean => {
    const widthOfExtendedButton = languageSwitcher.clientWidth;
    const padding =
        parseFloat(window.getComputedStyle(tabWrapper).paddingLeft) +
        parseFloat(window.getComputedStyle(tabWrapper).paddingRight);
    const widthOfFirstTab = firstTab.clientWidth;
    return widthOfFirstTab + widthOfExtendedButton + padding + BUFFER > tabWrapper.clientWidth;
};

const toggleLanguageSwitcherVisibility = (
    languageSwitcherListElement: HTMLElement,
    tabCount: number,
    totalTabs: number
) => {
    if (tabCount === totalTabs) {
        hideElement(languageSwitcherListElement);
    } else {
        showElement(languageSwitcherListElement);
    }
};

const addBorderToLastTab = (languageSwitcherList: HTMLElement) => {
    const lastTab = languageSwitcherList.lastElementChild;
    if (lastTab) {
        lastTab.getElementsByTagName("a")[0].classList.add("border-b");
    }
};

const hideTranslationStatus = (tab: HTMLElement) => {
    const translationStatus = tab.querySelector(".translation-status");
    if (translationStatus) {
        translationStatus.classList.add("hidden");
    }
};

const hideLanguageName = (tab: HTMLElement) => {
    const languageName = (tab as HTMLElement).querySelector(".language-name");
    if (languageName) {
        languageName.classList.add("hidden");
    }
};

const showTranslationStatus = (tab: HTMLElement) => {
    const translationStatus = tab.querySelector(".translation-status");
    if (translationStatus) {
        if (translationStatus.classList.contains("hidden")) {
            translationStatus.classList.remove("hidden");
        }
    }
};

const showLanguageName = (tab: HTMLElement) => {
    const languageName = (tab as HTMLElement).querySelector(".language-name");
    if (languageName) {
        if (languageName.classList.contains("hidden")) {
            languageName.classList.remove("hidden");
        }
    }
};

const hideLanguageNames = () => {
    const languageSwitcherList = document.getElementById("language-switcher-list");
    const tabsInSwitcher = Array.from(languageSwitcherList.children);
    tabsInSwitcher.forEach((tab) => {
        hideTranslationStatus(tab as HTMLElement);
        hideLanguageName(tab as HTMLElement);
    });
};

const showLanguageNames = () => {
    const languageSwitcherList = document.getElementById("language-switcher-list");
    const tabsInSwitcher = Array.from(languageSwitcherList.children);
    tabsInSwitcher.forEach((tab) => {
        showLanguageName(tab as HTMLElement);
        showTranslationStatus(tab as HTMLElement);
    });
};

const renderLanguageTabs = () => {
    const globeElement = document.getElementById("language-switcher-globe");
    const textElement = document.getElementById("language-switcher-text");
    const tabWrapper = document.getElementById("tab-wrapper");
    const languageSwitcher = document.getElementById("language-switcher");
    const languageSwitcherListElement = languageSwitcher?.parentElement;
    const languageSwitcherList = document.getElementById("language-switcher-list");

    if (!tabWrapper || !languageSwitcher || !languageSwitcherListElement || !languageSwitcherList) {
        return;
    }

    hideElement(globeElement);
    showElement(textElement);
    showLanguageNames();

    const tabs = Array.from(tabWrapper.children).concat(Array.from(languageSwitcherList.children));
    const availableWidth = calculateAvailableWidth(tabWrapper, languageSwitcherListElement);

    let usedSpace = 0;
    let tabCount = 0;

    tabs.forEach((tab) => {
        const fits = fitsInAvailableWidth(tab, usedSpace, availableWidth);

        if (!fits && tab !== languageSwitcherListElement && tabCount > 0) {
            moveToLanguageSwitcherList(tab, languageSwitcherList);
        } else {
            moveToTabWrapper(tab, tabWrapper, languageSwitcherListElement);
            usedSpace += tab.clientWidth + getTabMargin(tab);
            tabCount += 1;
        }
    });

    if (isButtonTooWide(tabs[0], languageSwitcher, tabWrapper)) {
        showElement(globeElement);
        hideElement(textElement);
        hideLanguageNames();
    }

    toggleLanguageSwitcherVisibility(languageSwitcherListElement, tabCount, tabs.length);
    addBorderToLastTab(languageSwitcherList);
};

window.addEventListener("load", () => {
    renderLanguageTabs();
    window.addEventListener("resize", renderLanguageTabs);
});
