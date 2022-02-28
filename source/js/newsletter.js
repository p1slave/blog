const modal = document.querySelector(".modal");
const trigger = document.querySelector(".trigger");
const closeButton = document.querySelector(".close-button");
const email = document.querySelector('.email');

// var validateEmail = function(elementValue) {
//     var emailPattern = /^[a-zA-Z0-9._-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,4}$/;
//     return emailPattern.test(elementValue);
// }

// $("input[name='email']").keyup(function() {
 
//     var value = $(this).val();
//     var valid = validateEmail(value);
 
//     if (!valid) {
//         $(this).css('color', 'red');
//  		$('.addbut1').prop('disabled', true);
//     } else {
//         $(this).css('color', '#2bb673');
//  		$('.addbut1').prop('disabled', false);
//     }
// });

function toggleModal() {
    modal.classList.toggle("show-modal");
}

function windowOnClick(event) {
    if (event.target === modal) {
        toggleModal();
    }
}

trigger.addEventListener("click", toggleModal);
closeButton.addEventListener("click", toggleModal);
window.addEventListener("click", windowOnClick);