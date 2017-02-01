$(document).ready(function() {
    $('#edit-debt-form').submit(function(event) {
        event.preventDefault();
        var form = $(this);
        var formData = form.serializeArray();
        $.ajax({
            url: form.attr('action'),
            data: formData,
            type: 'POST',
            success: function(response) {
                if (response && response.result === 'Ok') {
                    showSuccessPopup('Debt updated successfully!')
                }
                else if (response && response.errors) {
                    showErrorPopup(response.errors);
                }
            }
        });
    });
});