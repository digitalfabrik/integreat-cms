window.addEventListener("load", () => {
    const paginationChoice = document.getElementById("chunk-size") as HTMLSelectElement;
    if (paginationChoice) {
        paginationChoice.addEventListener("change", () => {
            if (paginationChoice.value) {
                window.location.href = paginationChoice.value;
            }
        });
    }
});
