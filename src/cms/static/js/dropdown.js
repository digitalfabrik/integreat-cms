/* loop through all dropdown buttons in _base.html 
to toggle between hiding and showing dropdown content*/

var activeElement = document.querySelector(".active");
var successorElement = activeElement.nextElementSibling;
if (successorElement != null && successorElement.classList.contains("dropdown-container")){
    successorElement.style.display = "flex";
} else if (activeElement.parentNode != null && activeElement.parentNode.classList.contains("dropdown-container")){
    var priorElement = activeElement.parentNode;
    priorElement.style.display = "flex";
    activeElement.classList.add("active");
    activeElement.parentElement.previousElementSibling.classList.remove("active");
}
