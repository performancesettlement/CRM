$(document).ready(function() {
    $('#profile-chooser').change(function() {
        var newVal = $(this).val();
        if (newVal == '') {
            redirect(addFeeProfileUrl);
        } else {
            redirect(editFeeProfileUrl.replace('0', newVal));
        }
    });
    showErrorPopup(formErrors);
});