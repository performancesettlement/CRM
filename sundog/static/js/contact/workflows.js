$(document).ready(function() {
    $('#add-stage-button').click(function(){
        $('#add-stage').show();
        $('#add-status').hide();
    });

    $('#add-status-button').click(function(){
        $('#add-status').show();
        $('#add-stage').hide();
    });

    $('#add-status-form').submit(function(event){
        event.preventDefault();
        var form = $(this);
        var formData = form.serializeArray();
        $.post(form.attr('action'), formData, function(response) {
            if (response.errors) {
                showErrorPopup(form_errors);
            }
            if (response.result) {
                refreshScreen();
            }
        });
    });

    $('#add-stage-form').submit(function(event){
        event.preventDefault();
        var form = $(this);
        var formData = form.serializeArray();
        $.post(form.attr('action'), formData, function(response) {
            if (response.errors) {
                showErrorPopup(form_errors);
            }
            if (response.result) {
                refreshScreen();
            }
        });
    });

});