window.addEventListener('load', () => {
    document.querySelectorAll('[data-enable-row-checkbox-toggle] tr').forEach(row => row.addEventListener('click', ({target}) => {
        if(target instanceof HTMLElement && !(target instanceof HTMLInputElement) && !(target instanceof HTMLAnchorElement) && !target.closest('.toggle-feedback-comment')) {
            const checkbox = row.querySelector('input');
            checkbox.checked = !checkbox.checked;
        }
    }));
});
