$(document).ready(function() {
    $('#delete-fee-profile').click(function(event) {
        event.preventDefault();
        var url = $(this).prop('href');
        showConfirmationDeletePopup(
            'There might be related enrollment plans that will be deleted. You will not be able to recover this data!',
            function() {
                $.ajax({
                    url: url,
                    beforeSend: function(xhr) {
                        xhr.setRequestHeader('X-CSRFToken', csrfToken);
                    },
                    type: 'DELETE',
                    success: function(response) {
                        if (response && response.result === 'Ok') {
                            showSuccessPopup('Fee profile deleted.');
                            redirect(addFeeProfileUrl);
                        }
                        else {
                            showErrorPopup('An error occurred deleting the fee profile.');
                        }
                    }
                });
            },
            false
        );
    });

    $('#profile-chooser').change(function() {
        var newVal = $(this).val();
        if (newVal == '') {
            redirect(addFeeProfileUrl);
        } else {
            redirect(editFeeProfileUrl.replace('0', newVal));
        }
    });

    $('#edit-fee-profile-form').submit(function(event) {
        event.preventDefault();
        var form = $(this);
        var formData = form.serializeArray();
        $.post(form.attr('action'), formData, function(response) {
            if (response.errors) {
                showErrorPopup(response.errors);
            }
            if (response.result == 'Ok') {
                var newName = $('#id_name').val();
                $('option[selected="selected"]').html(newName);
                showSuccessPopup('Fee profile updated.');
            }
        });
    });

    showErrorPopup(formErrors);
});