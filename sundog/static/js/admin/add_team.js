$(document).ready(function() {
    $('#select-team').change(function() {
        var val = $(this).val();
        if (val !== '') {
            redirect(editTeamUrl.replace('0', val));
        }
        else {
            redirect(addTeamUrl);
        }
    });

    $('#save-team').click(function() {
        var form = $('#add-team-form');
        var formData = form.serializeArray();
        $.ajax({
            url: form.attr('action'),
            data: formData,
            type: 'POST',
            success: function(response) {
                if (response.errors) {
                    showErrorPopup(response.errors);
                }
                if (response.result === 'Ok') {
                    $('#select-team').append('<option value="' + response.id + '">' + response.name + '</option>');
                    $('select').val('');
                    showSuccessPopup('Team successfully created!');
                }
            }
        });
    });
});