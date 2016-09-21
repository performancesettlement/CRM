$(document).ready(function() {
    function toggleInputValues(selector, disabled) {
        var elem = $(selector);
        if (disabled) {
            elem.hide();
            elem.find('input, select').attr('disabled','disabled');
        } else {
            elem.show();
            elem.find('input, select').removeAttr('disabled');
        }
    }

    $('#add-second-fee').click(function() {
        $(this).hide();
        $('#cancel-second-fee').show();
        toggleInputValues('#fee-2-data', false);
    });

    $('#cancel-second-fee').click(function() {
        $(this).hide();
        $('#add-second-fee').show();
        toggleInputValues('#fee-2-data', true);
    });

    if (!hasSecondFee) {
        toggleInputValues('#fee-2-data', true);
    }

    $('#plan-chooser').change(function() {
        var newVal = $(this).val();
        if (newVal == '') {
            redirect(addEnrollmentPlanUrl);
        } else {
            redirect(editEnrollmentPlanUrl.replace('0', newVal));
        }
    });

    $('#delete-enrollment-plan').click(function(event) {
        event.preventDefault();
        var url = $(this).prop('href');
        showConfirmationPopup(
            'There might be related ongoing enrollments that will be deleted. You will not be able to recover this data!',
            function() {
                $.ajax({
                    url: url,
                    beforeSend: function(xhr) {
                        xhr.setRequestHeader('X-CSRFToken', csrfToken);
                    },
                    type: 'DELETE',
                    success: function(response) {
                        if (response && response.result === 'Ok') {
                            showSuccessPopup('Enrollment plan deleted.');
                            redirect(addEnrollmentPlanUrl);
                        }
                        else {
                            showErrorPopup('An error occurred deleting the enrollment plan.');
                        }
                    }
                });
            }
        );
    });

    $('#edit-enrollment-plan-form').submit(function(event) {
        event.preventDefault();
        var form = $(this);
        var formData = form.serializeArray();
        $.post(form.attr('action'), formData, function(response) {
            if (response.errors) {
                showErrorPopup(response.errors);
            }
            if (response.result == 'Ok') {
                showSuccessPopup('Enrollment plan updated.');
            }
        });
    });

    showErrorPopup(formErrors);
});