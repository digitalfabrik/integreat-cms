/*
 * Takes a list of boxes and calculates an even distribution into two columns
 */
const findPartition = (boxes: Array<HTMLElement>) => {
    // Remember the box heights so we don't have to calculate them for every recursion step
    const boxesHeights: Map<HTMLElement, number> = new Map(boxes.map((box) => [box, box.offsetHeight]));
    console.debug("Sidebar boxes and their heights:", boxesHeights);

    // Initialize buffers which are updated from inside the recursive function
    let column: Array<HTMLElement> = [];
    let columnHeight = 0;

    // The ideal distribution would be exactly 50:50
    const sum: number = Array.from(boxesHeights.values()).reduce(
        (accumulator: number, currentValue: number) => accumulator + currentValue,
        0
    );
    const maxHeight: number = sum / 2;

    // Recurse into every possible combination of boxes to find
    // the distribution which is closest to the target height
    const findRecursive = (columnBuffer: Array<HTMLElement>, heightBuffer: number) => {
        if (heightBuffer > columnHeight) {
            column = columnBuffer;
            columnHeight = heightBuffer;
        }
        boxesHeights.forEach((height: number, box: HTMLElement) => {
            if (!columnBuffer.includes(box) && heightBuffer + height <= maxHeight) {
                findRecursive(columnBuffer.concat([box]), heightBuffer + height);
            }
        });
    };
    findRecursive([], 0);

    // All remaining boxes are assigned to the larger column
    const largerColumn = boxes.filter((x) => !column.includes(x));
    console.debug("Sidebar boxes in larger column:", largerColumn);
    console.debug("Sidebar boxes in smaller column:", column);
    return [largerColumn, column];
};
