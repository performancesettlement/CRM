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
        var form = $('#edit-team-form');
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
                    showSuccessPopup('Team successfully updated!');
                }
            }
        });
    });

    $('#delete-team').click(function() {
        showConfirmationPopup(
            'There are relations depending on this team that will be deleted, this data cannot be recovered!',
            'Yes, delete',
            function() {
                $.ajax({
                    url: deleteTeamUrl,
                    beforeSend: function(xhr) {
                        xhr.setRequestHeader('X-CSRFToken', csrfToken);
                    },
                    type: 'DELETE',
                    success: function(response) {
                        if (response.errors) {
                            showErrorPopup(response.errors);
                        }
                        if (response.result === 'Ok') {
                            redirect(addTeamUrl);
                        }
                    }
                });
            },
            false
        );
    });
});