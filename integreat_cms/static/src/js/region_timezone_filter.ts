// Live-filter the timezone <select> by the selected timezone area.
// Pure UI; doesn't change how saving works.
document.addEventListener("DOMContentLoaded", () => {
  const area = document.getElementById("id_timezone_area") as HTMLSelectElement | null;
  const tz = document.getElementById("id_timezone") as HTMLSelectElement | null;
  if (!area || !tz) { return; }

  // Cache all original options (including the first "---------" one)
  const allOptions = Array.from(tz.options).map((opt) => ({ value: opt.value, label: opt.text }));

  // eslint-disable-next-line prefer-arrow/prefer-arrow-functions
  function applyFilter(selectedArea: string | null) {
    const currentValue = tz.value;

    const filtered = allOptions.filter((opt, idx) => {
      if (idx === 0) { return true; } // keep placeholder
      if (!selectedArea) { return true; } // no area -> show all
      return opt.value && opt.value.startsWith(`${selectedArea}/`);
    });

    tz.innerHTML = "";
    for (const opt of filtered) {
      const o = document.createElement("option");
      o.value = opt.value;
      o.text = opt.label;
      tz.add(o);
    }

    // keep previous selection if it's still in the filtered list
    if (filtered.some((opt) => opt.value === currentValue)) {
      tz.value = currentValue;
    } else {
      tz.value = "";
    }
  }

  // Initial filter on load + re-filter on change
  applyFilter(area.value || null);
  area.addEventListener("change", () => applyFilter(area.value || null));
});
