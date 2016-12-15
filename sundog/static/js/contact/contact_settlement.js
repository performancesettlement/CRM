$(document).ready(function() {
    $('#generate-payments').click(function(event) {
        event.preventDefault();
        var payments = $('#id_payments').val();
        var startDate = $('#id_start_date').val();
        var url = baseContactSettlementUrl + '?payments=' + payments + '&start_date=' + startDate;
        redirect(url);
    });

    $('#id_no_payments').change(function() {
        var checked = $(this).prop('checked');
        var paymentsContainer = $('#payment-container');
        var inputsAndSelects = paymentsContainer.find('input, select');
        if (checked) {
            paymentsContainer.hide();
            inputsAndSelects.attr('disabled', true);
        }
        else {
            paymentsContainer.show();
            inputsAndSelects.removeAttr('disabled');
        }
    });

    $('#settlement-form').submit(function(event) {
        event.preventDefault();
        var form = $(this);
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
                    redirect(settlementOfferUrl);
                }
            }
        });
    });
});