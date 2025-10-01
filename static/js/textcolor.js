function updateTextColor() {
    var tdElements = document.getElementsByClassName('invisibility');
    for (var i = 0; i < tdElements.length; i++) {
        if (tdElements[i].textContent === '隐藏') {
            tdElements[i].classList.add('redtext');
        }
    }
    for (var i = 0; i < tdElements.length; i++) {
        if (tdElements[i].textContent === "None" || tdElements[i].textContent === 'null') {
            tdElements[i].classList.add('greentext');
            tdElements[i].textContent = '显示';
        }
    }
    for (var i = 0; i < tdElements.length; i++) {
        if (tdElements[i].textContent === '过期') {
            tdElements[i].classList.add('yellowtext');
        }
    }

    var tdElements_birthday = document.getElementsByClassName('birthday');
    for (var i = 0; i < tdElements_birthday.length; i++) {
        if (tdElements_birthday[i].textContent === 'None' || tdElements_birthday[i].textContent === 'null') {
            tdElements_birthday[i].classList.add('redtext');
            tdElements_birthday[i].textContent = '非生日';
        }
    }
    for (var i = 0; i < tdElements_birthday.length; i++) {
        if (tdElements_birthday[i].textContent === 'on') {
            tdElements_birthday[i].classList.add('greentext');
            tdElements_birthday[i].textContent = '生日';
        }
    }
}

document.addEventListener('DOMContentLoaded', function () {
    updateTextColor();  
});
