document.addEventListener("DOMContentLoaded", function () {
  var hiddenInput = document.querySelector('input[name="birthday_status"]');
  var checkbox = document.querySelector('input[name="birthday"]');

  if (hiddenInput && hiddenInput.value === 'on' && checkbox) {
    checkbox.checked = true;
  }
});
