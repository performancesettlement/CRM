$(document).ready(function() {
    var inputs = $('input');

    function updateTotals(data) {
        $('#incomes-total').html(data.incomes_total);
        $('#expenses-total').html(data.expenses_total);
        $('#dti').html(data.dti);
        $('#cash-flow').html(data.cash_flow);
        $('#assets-total').html(data.assets);
    }

    if (!editPermission) {
        inputs.attr('disabled', 'disabled');
    }
    inputs.change(function(event) {
        if (editPermission) {
            if ($(this).val() == '') {
                $(this).val(0)
            }
            else {
                var form = $('#budget-form');
                var formData = form.serializeArray();
                $.post(form.attr('action'), formData, function(response) {
                    if (response.errors) {
                        showErrorPopup(response.errors);
                    }
                    if (response.result) {
                        updateTotals(response);
                        showSuccessToast('Budget info successfully updated!');
                    }
                });
            }
        }
        else {
            showErrorToast("You don't have permission to edit this!");
        }
    });

    $('#budget-delete').click(function(event) {
        event.preventDefault();
        var url = $(this).prop('href');
        showConfirmationDeletePopup(
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
                            showSuccessPopup('Budget info successfully deleted!');
                        }
                        else {
                            showErrorPopup('An error occurred deleting the the budget info.');
                        }
                    }
                });
            },
            false
        );
    });
});