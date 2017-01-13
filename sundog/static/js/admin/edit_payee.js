$(document).ready(function() {
    $('#edit-payee-form').submit(function(event) {
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
                    var row = $('#payee-' + response.payee_id);
                    var defaultForCompany = row.find('.default-for-company');
                    if (response.default_for_company) {
                        defaultForCompany.addClass('green');
                        defaultForCompany.removeClass('red');
                    }
                    else {
                        defaultForCompany.addClass('red');
                        defaultForCompany.removeClass('green');
                    }
                    row.find('.name').html(response.name);
                    row.find('.bank-name').html(response.bank_name);
                    row.find('.routing-number').html(response.routing_number);
                    row.find('.account-number').html(response.account_number);
                    row.find('.account-type').html(response.account_type);
                    row.find('.name-on-account').html(response.name_on_account);
                    showSuccessPopup('Payee successfully updated!');
                }
            }
        });
    });
});