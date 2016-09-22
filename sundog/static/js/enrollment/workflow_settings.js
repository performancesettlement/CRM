$(document).ready(function() {
    $('#type-chooser').change(function() {
        var newVal = $(this).val();
        redirect(workflowSettingsUrl + '?type=' + newVal);
    });

    $('#save-settings').click(function(event) {
        event.preventDefault();
        var form = $('#workflow-settings-form');
        var formData = form.serializeArray();
        formData.push({name: 'type', value: $('#type-chooser').val()});
        $.post(form.attr('action'), formData, function(response) {
            if (response.errors) {
                showErrorPopup(response.errors);
            }
            if (response.result == 'Ok') {
                showSuccessPopup('Settings updated.');
            }
        });
    });
});