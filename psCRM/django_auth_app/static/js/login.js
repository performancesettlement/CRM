$(document).ready(function(){
    var tz = jstz.determine();
    //console.log(tz.name());
    $('#id_timezone').val(tz.name());
    showErrorPopup(form_errors);
    $("#username").on('blur keyup', function() {
        var username = $(this);
        if(username.val().length){
            username.val(username.val().toLowerCase())
        }
    });
});
