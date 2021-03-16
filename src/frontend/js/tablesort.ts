import Tablesort from "tablesort";
(window as any).Tablesort = Tablesort;
import "tablesort/src/sorts/tablesort.date.js";
import "tablesort/src/sorts/tablesort.number.js";
import "tablesort/tablesort.css";
import "../css/tablesort.css";

document
  .querySelectorAll("[data-enable-table-sort]")
  .forEach((node) => new Tablesort(node as HTMLElement));
