$(document).ready(function() {
    function hideForms() {
        var forms = $('#forms');
        forms.children().each(function() {
            $(this).hide();
        });
    }

    function cleanForms() {
        var forms = $('#forms');
        forms.children().each(function() {
            var form = $(this);
            form.find('input').val('');
            form.find('select').val('');
        });
    }

    hideForms();

    $('.edit-debt').click(function(event) {
        event.preventDefault();
        var debtId = parseInt($(this).attr('id'));
        var originalCreditor = parseInt($('#' + debtId + '-original-creditor').attr('value'));
        var originalCreditorAccountNumber = $('#' + debtId + '-original-creditor-account-number').attr('value');
        var debBuyerElem = $('#' + debtId + '-debt-buyer');
        var debtBuyer = debBuyerElem.attr('value') ? parseInt(debBuyerElem.attr('value')) : '';
        var debtBuyerAccountNumber = $('#' + debtId + '-debt-buyer-account-number').attr('value');
        var accountType = $('#' + debtId + '-account-type').attr('value');
        var originalDebtAmount = $('#' + debtId + '-original-debt-amount').attr('value');
        var currentDebtAmount = $('#' + debtId + '-current-debt-amount').attr('value');
        var currentPayment = $('#' + debtId + '-current-payment').attr('value');
        var whoseDebt = $('#' + debtId + '-whose-debt').attr('value');
        var lastPaymentDate = $('#' + debtId + '-last-payment-date').attr('value');
        var hasSummons = $('#' + debtId + '-has-summons').attr('value');
        var summonsDate = $('#' + debtId + '-summons-date').attr('value');
        var courtDate = $('#' + debtId + '-court-date').attr('value');
        var discoveryDate = $('#' + debtId + '-discovery-date').attr('value');
        var answerDate = $('#' + debtId + '-answer-date').attr('value');
        var serviceDate = $('#' + debtId + '-service-date').attr('value');
        var paperworkReceiveDate = $('#' + debtId + '-paperwork-received-date').attr('value');
        var poaSentDate = $('#' + debtId + '-poa-sent-date').attr('value');
        var form = $('#edit-debt-form');
        form.find('#id_debt_id').val(debtId);
        form.find('#id_original_creditor').val(originalCreditor);
        form.find('#id_original_creditor_account_number').val(originalCreditorAccountNumber);
        form.find('#id_debt_buyer').val(debtBuyer);
        form.find('#id_debt_buyer_account_number').val(debtBuyerAccountNumber);
        form.find('#id_account_type').val(accountType);
        form.find('#id_original_debt_amount').val(originalDebtAmount);
        form.find('#id_current_debt_amount').val(currentDebtAmount);
        form.find('#id_current_payment').val(currentPayment);
        form.find('#id_whose_debt').val(whoseDebt);
        form.find('#id_last_payment_date').val(lastPaymentDate);
        form.find('#id_has_summons').val(hasSummons);
        form.find('#id_summons_date').val(summonsDate);
        form.find('#id_court_date').val(courtDate);
        form.find('#id_discovery_date').val(discoveryDate);
        form.find('#id_answer_date').val(answerDate);
        form.find('#id_service_date').val(serviceDate);
        form.find('#id_paperwork_received_date').val(paperworkReceiveDate);
        form.find('#id_poa_sent_date').val(poaSentDate);
        hideForms();
        $('#edit-debt').show();
    });

    $('.cancel').click(function() {
        hideForms();
        cleanForms();
    });

    $('#add-debt-button').click(function() {
        hideForms();
        $('#add-debt').show();
    });

    $('.form').submit(function(event) {
        event.preventDefault();
        var form = $(this);
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

    $('.move-page').click(function() {
        var button = $(this);
        var page = button.html();
        $('input[name=page]').val(page);
        $('#search-form').submit();
    });

    $('.prev-page').click(function() {
        var input = $('input[name="page"]');
        var prevPage = parseInt(input.val()) - 1;
        input.val(prevPage);
        $('#search-form').submit();
    });

    $('.next-page').click(function() {
        var input = $('input[name="page"]');
        var nextPage = parseInt(input.val()) + 1;
        input.val(nextPage);
        $('#search-form').submit();
    });
});
