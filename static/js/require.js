document.addEventListener("DOMContentLoaded", function () {
    var birthdayCheckbox = document.getElementById("birthdayCheckbox");
    var targetInput = document.getElementById("targetInput");

    if (birthdayCheckbox && targetInput) {
        birthdayCheckbox.addEventListener("change", function () {
            if (birthdayCheckbox.checked) {
                // 如果选中了"是否生日歌"，将"点给谁"字段设置为必填
                targetInput.required = true;
            } else {
                // 如果未选中"是否生日歌"，将"点给谁"字段设置为非必填
                targetInput.required = false;
            }
        });
    } else {
        console.error("error");
    }
});
