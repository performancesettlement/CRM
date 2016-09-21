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
    showErrorPopup(formErrors);
});