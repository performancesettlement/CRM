$(document).ready(function() {
    $('#preview-button').click(function() {
        var settlementId = $('#debt-selector').val();
        var url = schedulePerformanceFeesUrl;
        if (settlementId) {
            url += '?settlement_id=' + settlementId;
        }
        redirect(url);
    });

    function getPaymentForms() {
        var settlementId = $('#debt-selector').val();
        var url = schedulePerformanceFeesUrl + '?settlement_id=' + settlementId;
        var paymentsIndexes = [];
        var paymentsStartDates = [];
        $('.payees').each(function(){
            var payee = $(this);
            var payment = payee.find('.payments-selector').prop('selectedIndex');
            paymentsIndexes.push(payment);
            var startDate = payee.find('.start-date').val();
            paymentsStartDates.push(startDate);
        });
        paymentsIndexes = '&p_number=' + paymentsIndexes.join('&p_number=');
        paymentsStartDates = '&p_dates=' + paymentsStartDates.join('&p_dates=');
        url += paymentsIndexes + paymentsStartDates;
        $.ajax({
            url: url,
            type: 'GET',
            success: function(response) {
                if (response.forms) {
                    $('.payees').each(function() {
                        var payee = $(this);
                        var payeeId = payee.attr('id').replace('payee-', '');
                        var forms = response.forms[payeeId];
                        var feePaymentsContainer = payee.find('.fee-payments');
                        feePaymentsContainer.html('');
                        feePaymentsContainer.html(forms.join(''));
                    });
                }
            }
        });
    }

    $('.start-date, .payments-selector').change(function() {
        getPaymentForms();
    });
});