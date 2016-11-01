$(document).ready(function() {

    function getOptions(fee) {
        var options = '';
        for (var i = 0; i < fee.options.length; i++) {
            var option = fee.options[i];
            options += '<option value="' + option[0] + '">' + option[1] + '</option>';
        }
        return options;
    }

    function getDebtIds(){
        var debtsIds = '';
        $('#debts-table').find('tr').each(function() {
            var debt = $(this);
            if (debt.hasClass('enrolled')) {
                if (debtsIds != '') {
                    debtsIds += ',';
                }
                debtsIds += debt.attr('id');
            }
        });
        return debtsIds;
    }

    function createSelector(fee, i) {
        var options = getOptions(fee);
        var feeHtml = '<div class="m-b-xs">' +
            '<label>' + fee.name + ':</label>' +
            '<input type="hidden" name="' + i + '-fee_plan" value="' + fee.fee_plan_id + '">' +
            '<select id="id_' + i + '-amount" name="' + i + '-amount" class="fee-select">' +
                options +
            '</select>' +
        '</div>';
        return feeHtml;
    }

    function addTableHeaderBefore(elem, fee) {
        elem.before('<th class="dynamic-added">' + fee.name + '</th>');
    }

    function addTableFooterBefore(elem, fee) {
        var footer = $('#' + fee.name + '-footer');
        if (footer.length > 0) {
            footer.html(fee.amount);
        }
        else {
            elem.before('<td id="' + fee.name + '-footer" class="dynamic-added">' + fee.amount + '</td>');
        }
    }

    function generateSelectorsAndAddTableHeader(fees, table) {
        var lastHeader = table.find('thead tr th.savings');
        for (var i = 0; i < fees.length; i++) {
            var fee = fees[i];
            var feeHtml = createSelector(fee, i + 1);
            addTableHeaderBefore(lastHeader, fee);
            $('#fees').append(feeHtml);
        }
    }

    function refreshFooterTotals(fees, table) {
        var lastFooter = table.find('tfoot tr td.footer-total-savings');
        for (var i = 0; i < fees.length; i++) {
            var fee = fees[i];
            addTableFooterBefore(lastFooter, fee)
        }
    }

    function generatePayments(payments, fees, table) {
        var body = table.find('tbody');
        body.html('');
        for (var i = 0; i < payments.length; i++) {
            var payment = payments[i];
            var feeRows = '';
            for (var j = 0; j < fees.length; j++) {
                var fee = fees[j];
                feeRows += '<td class="fee" name="' + fee.name + '">' + payment[fee.name] + '</td>';
            }
            var row = '<tr class="payment">';
            row += '<td class="number">' + payment.order + '</td>';
            row += '<td class="date">' + payment.date + '</td>';
            row += feeRows;
            row += '<td>' + payment.savings + '</td>';
            row += '<td class="amount">' + payment.payment + '</td>';
            row += '<td>' + payment.acct_balance + '</td>';
            row += '</tr>';
            body.append(row);
        }
    }

    function clearTableHeader(table) {
        table.find('thead tr th.dynamic-added').remove();
    }

    function clearTableFooter(table) {
        table.find('tfoot tr td.dynamic-added').remove();
    }

    function clearTableBody(table) {
        table.find('tbody').children().remove();
    }

    function clearFeesTotal() {
        $('#total-fees').html(('$0.00'));
        $('#est-client-savings').html($('#est-client-savings-with-no-fees').html());
    }

    function clearFeesDropdowns(){
        $('#fees').html('');
    }

    function refreshTotals(data) {
        $('#est-client-savings').html(data.total_savings);
        $('#est-client-savings-with-no-fees').html(data.total_savings);
        $('#total-fees').html(data.total_fees);
        $('#est-sett-dollars').html(data.total_sett);
        $('#total-debt').html(data.total_debt);
    }

    function selectProgramLength(length) {
        $('#id_program_length').val(length);
    }

    function setProgramLengthOptions(options) {
        var optionsHtml = '';
        for (var i = 0; i < options.length; i++) {
            var option = options[i];
            optionsHtml += '<option value="' + option[0] + '">' + option[1] + '</option>';
        }
        $('#id_program_length').html(optionsHtml);
    }

    function setDates(data) {
        $('#id_start_date').val(data.start_date);
        var firstDateInput = $('#id_first_date');
        var firstDateContainer = $('#first-payment-date');
        if (data.select_first_date) {
            firstDateContainer.show();
            firstDateInput.prop('disabled', false);
            firstDateInput.val(data.first_date);
        }
        else {
            firstDateContainer.hide();
            firstDateInput.prop('disabled', true);
        }
        var secondDateInput = $('#id_second_date');
        var secondDateContainer = $('#second-payment-date');
        if (data.second_date) {
            secondDateContainer.show();
            secondDateInput.val(data.second_date);
        }
        else {
            secondDateContainer.hide();
            secondDateInput.val('');
        }
    }

    function setFooterTotals(data, table) {
        $('.footer-total-savings').html(data.total_savings);
        $('.footer-total-payment').html(data.total_payment);
        refreshFooterTotals(data.fees, table);
    }

    function refreshEnrollmentScreen(data, programLengthContainer, table, refreshAll) {
        var fees = data.fees;
        setDates(data);
        refreshTotals(data);
        generatePayments(data.payments, fees, table);
        setFooterTotals(data, table);
        if (refreshAll) {
            generateSelectorsAndAddTableHeader(fees, table);
            setProgramLengthOptions(data.program_lengths);
            selectProgramLength(data.length_selected);
        }
        programLengthContainer.show();
    }

    function requestEnrollmentPlanInfo(sendExtraFields, refreshAll) {
        var planId = $('#id_enrollment_plan').val();
        var table = $('#payments-table');
        var programLengthContainer = $('#edit-program-length-container');
        if (planId !== '') {
            var url = getEnrollmentPlanInfoUrl.replace('0', planId);
            var debtsIds = getDebtIds();
            var recurringDate = $('#id_start_date').val();
            url += '?start_date=' + recurringDate + '&debt_ids=' + debtsIds;
            if (sendExtraFields) {
                var firstDate = '';
                var firstDateInput = $('#id_first_date');
                if (firstDateInput.val()) {
                    firstDate = firstDateInput.val();
                }
                var secondDate = $('#id_second_date').val();
                var monthsSelector = $('#id_program_length');
                var months = monthsSelector.val() != null ? monthsSelector.val() : '';
                url += '&first_date=' + firstDate + '&second_date=' + secondDate + '&months=' + months;
                var fees = $('.fee-select');
                if (fees.length > 0) {
                    for (var i = 0; i < fees.length; i++) {
                        var fee = $(fees[i]);
                        url += '&' + fee.attr('id') + '=' + fee.val();
                    }
                }
            }
            if (refreshAll) {
                clearTableHeader(table);
                clearTableFooter(table);
                clearTableBody(table);
                clearFeesDropdowns();
            }
            $.get(url, function(response) {
                if (response.data) {
                    refreshEnrollmentScreen(response.data, programLengthContainer, table, refreshAll);
                }
            });
        }
        else {
            clearFeesTotal();
            programLengthContainer.hide();
        }
    }

    function requestDebtsInfo() {
        var url = getDebtsInfoUrl;
        var debtsIds = getDebtIds();
        url += '?debt_ids=' + debtsIds;
        var table = $('#payments-table');
        clearTableHeader(table);
        clearTableFooter(table);
        clearTableBody(table);
        clearFeesDropdowns();
        var programLengthContainer = $('#edit-program-length-container');
        programLengthContainer.hide();
        $.get(url, function(response) {
            if (response.data) {
                refreshTotals(response.data);
            }
        });
    }

    function anySelectedDebts() {
        var checked = $('input.debt:checked');
        return checked.length > 0;
    }

    $('#id_program_length').change(function(e) {
        if (e.originalEvent) {
            requestEnrollmentPlanInfo(true, false);
        }
    });

    $('#id_first_date').change(function(e) {
        if (e.originalEvent) {
            requestEnrollmentPlanInfo(true, false);
        }
    });

    $('#id_start_date').change(function(e) {
        if (e.originalEvent) {
            requestEnrollmentPlanInfo(true, false);
        }
    });

    $('#fees').on('change', '.fee-select', function(e) {
        if (e.originalEvent) {
            requestEnrollmentPlanInfo(true, false);
        }
    });

    $('#enrollment-form-submit').click(function() {
        var form = $('#enrollment-form');
        var formData = form.serializeArray();
        var body = $('#payments-table').find('tbody tr.payment');
        var prefix = 3;
        body.each(function() {
            var number = parseInt($(this).find('td.number').html());
            var date = $(this).find('td.date').html();
            var amount = $(this).find('td.amount').html().replace('$', '').replace(',', '');
            var fees = $(this).find('td.fee');
            var prefixStr = prefix + '-';
            fees.each(function(){
                var name = prefixStr + $(this).attr('name');
                var value = $(this).html().replace('$', '').replace(',', '');
                formData.push({'name': name, 'value': value});
            });
            formData.push({name: prefixStr + 'date', value: date});
            formData.push({name: prefixStr + 'amount', value: amount});
            prefix++;
        });

        $.ajax({
            url: form.attr('action'),
            data: formData,
            type: 'POST',
            success: function(response){
                if (response.errors) {
                    showErrorPopup(response.errors);
                }
                if (response.result === 'Ok' && response.redirect_url) {
                    redirect(response.redirect_url);
                }
            }
        });
    });

    $('input.debt').change(function() {
        $(this).parent().parent().toggleClass('enrolled');
        if (anySelectedDebts()) {
            var planId = $('#id_enrollment_plan').val();
            if (planId !== '') {
                requestEnrollmentPlanInfo(true, true);
            }
            else {
                requestDebtsInfo();
            }
        }
        else {
            $(this).parent().parent().toggleClass('enrolled');
            $(this).prop('checked', true);
            showErrorPopup("You can't disable all debts.");
        }
    });



    $('#id_enrollment_plan').change(function() {
        var planId = $('#id_enrollment_plan').val();
        if (planId !== '') {
            requestEnrollmentPlanInfo(false, true);
        }
        else {
            requestDebtsInfo();
        }
    });
});