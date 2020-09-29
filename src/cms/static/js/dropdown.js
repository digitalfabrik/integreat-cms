/**
 * selects the current active html tags and
 * checks weather successor element contains a dropdown container
 */

var activeElement = document.querySelector(".active");
var successorElement = activeElement.nextElementSibling;
if (successorElement != null && successorElement.classList.contains("dropdown-container")){
    successorElement.style.display = "flex";
}
