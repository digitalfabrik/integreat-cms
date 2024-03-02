window.addEventListener("load", () => {
    // event handler to toggle form fields
    const toggleables = [
        ["id_statistics_enabled", "statistics-toggle-div"],
        ["id_mt_addon_booked", "mt-toggle-div"],
        ["id_mt_midyear_start_enabled", "mt-renewal-toggle-div"],
        ["id_automatic_translation", "language-options"],
        ["id_schedule_send", "push_notification_schedule"],
        ["id_is_template", "push_notification_template_name"],
    ];
    toggleables.forEach((it) => {
        const toggleControl = document.getElementById(it[0]);
        const toBeToggled = document.getElementById(it[1]);

        // remove "hidden" if toggleControl is already checked on page load
        if ((toggleControl as HTMLInputElement)?.checked) {
            toBeToggled.classList.remove("hidden");
        }
        if (toggleControl && toBeToggled) {
            toggleControl.addEventListener("change", ({ target }) => {
                if ((target as HTMLInputElement).checked) {
                    toBeToggled.classList.remove("hidden");
                } else {
                    toBeToggled.classList.add("hidden");
                }
            });
        }
    });
});
