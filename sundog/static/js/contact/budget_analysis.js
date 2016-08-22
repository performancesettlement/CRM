$(document).ready(function(){
    $('#budget-submit').click(function(event) {
        event.preventDefault();
        var form = $('#budget-form');
        var formData = form.serializeArray();
        $.post(form.attr('action'), formData, function(response) {
            if (response.errors) {
                showErrorPopup(response.errors);
            }
            if (response.result) {
                refreshScreen();
            }
        });
    });

    $('#budget-delete').click(function(event) {
        event.preventDefault();
        var url = $(this).prop('href');
        showConfirmationPopup(
            'You will not be able to recover this data!',
            function() {
                $.ajax({
                    url: url,
                    beforeSend: function(xhr) {
                        xhr.setRequestHeader("X-CSRFToken", csrfToken);
                    },
                    type: 'DELETE',
                    success: function(response) {
                        if (response && response.result === 'Ok') {
                            $('input').val(0);
                            showSuccessPopup('Budget info deleted.');
                        }
                        else {
                            showErrorPopup('An error occurred deleting the file.');
                        }
                    }
                });
            }
        );

    });
});