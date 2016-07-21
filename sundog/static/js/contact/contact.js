$(document).ready(function(){
    $('#template-chooser').change(function(){
        var value = $('#template-chooser').val();
        $('.form-template').hide();
        $('#' + value).show();
    });
});
