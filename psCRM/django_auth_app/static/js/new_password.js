$(document).ready(function(){

    $( "#id_password1" ).keyup(function() {
        var password = $(this).val();
        var password2 = $("#id_password2").val();
        validatePassword(password, password2);
    });

    $( "#id_password2" ).keyup(function() {
        var password2 = $(this).val();
        var password = $("#id_password1").val();
        validatePassword(password, password2);
    });

});

function validatePassword(password, password2){
    var score = 0;

    if(password.length) {
        //if password bigger than 5 give 1 point
        if (password.length > 5) score++;

        //if password has a letter characters give 1 point
        if (( password.match(/[a-z]/) ) || ( password.match(/[A-Z]/) )) score++;

        //if password has at least one number give 1 point
        if (password.match(/[1-9]/)) score++;

        //if password has at least one special caracther give 1 point
        if (password.match(/[`~!@#$%^&*()_|+\-=?;:'",.<>\{\}\[\]\\\/]/)) score++;

        if (password == password2) score++;
    }

    var label = "progress-bar"; var width="0";
    switch (score){
        case 1: label = "progress-bar-danger"; width="5"; break;
        case 2: label = "progress-bar-warning"; width="25"; break;
        case 3: label = "progress-bar-info"; width="50"; break;
        case 4: label = "progress-bar-success"; width="75"; break;
        case 5: label = "progress-bar-navy-light"; width="100"; break;
    }

    var progress = $("#progress_bar");
    progress.removeClass();
    progress.addClass("progress-bar");
    if(label!="progress-bar")
        progress.addClass(label);
    progress.css("width", width+"%");
}