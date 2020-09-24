/* loop through all dropdown buttons in _base.html 
to toggle between hiding and showing dropdown content*/

var activeElement = document.querySelector(".active");
var successorElement = activeElement.nextElementSibling;
if (successorElement.classList.contains("dropdown-container")){
    successorElement.style.display = "flex";
}
