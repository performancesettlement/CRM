$(document).ready(function() {
    $('#settlement-offer-form').submit(function(event) {
        event.preventDefault();
        var checkedDebt = $('.debt-radio:checked');
        if (checkedDebt.length == 1) {
            var debtId = checkedDebt.attr('id').replace('debt-', '').replace('-radio', '');
            var form = $(this);
            var formData = form.serializeArray();
            formData.push({name: 'debt', value: debtId});
            $.ajax({
                url: form.attr('action'),
                data: formData,
                type: 'POST',
                success: function(response) {
                    if (response.errors) {
                        showErrorPopup(response.errors);
                    }
                    if (response.result === 'Ok') {
                        refreshScreen();
                    }
                }
            });
        }
        else {
            showErrorPopup('You must select a debt to make an offer to!');
        }
    });

    $('.debt-radio').change(function() {
        selectASingleRadioButton('.debt-radio', $(this));
        var debtId = $(this).attr('id').replace('debt-', '').replace('-radio', '');
        $.ajax({
            url: getDebtOfferUrl.replace('0', debtId),
            type: 'GET',
            success: function(offer) {
                var form = $('#settlement-offer-form');
                if (!$.isEmptyObject(offer)) {
                    form.append('<input id="id_settlement_offer_id" name="settlement_offer_id" type="hidden" value="'
                        + offer.settlement_offer_id + '">');
                    form.find('#id_made_by').val(offer.made_by);
                    form.find('#id_negotiator').val(offer.negotiator);
                    form.find('#id_status').val(offer.status);
                    form.find('#id_date').val(offer.date);
                    form.find('#id_valid_until').val(offer.valid_until);
                    form.find('#id_debt_amount').val(offer.debt_amount);
                    form.find('#id_offer_amount').val(offer.offer_amount);
                    form.find('#id_notes').val(offer.notes);
                }
                else {
                    form.trigger('reset');
                    form.find('#id_settlement_offer_id').remove();
                }
            }
        });
    });

    if (offerSaved) {
        showSuccessPopup('Offer successfully saved.');
    }
    if (debtId > 0) {
        $('#debt-' + debtId + '-radio').click();
    }
});