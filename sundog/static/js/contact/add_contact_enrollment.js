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
        var feeHtml = '<div>' +
            '<div>' +
                '<label>' + fee.name + ':</label>' +
                '<select id="id_' + i + '-amount" >' +
                    options +
                '</select>' +
            '</div>' +
        '</div>';
        return feeHtml;
    }

    function addTableHeaderBefore(elem, fee) {
        elem.before('<th class="dymamic-added">' + fee.name + '</th>');
    }

    function generateSelectorsAndAddTableHeaders(fees, table) {
        var last = table.find('thead tr th.savings');
        for (var i = 0; i < fees.length; i++) {
            var fee = fees[i];
            var feeHtml = createSelector(fee);
            addTableHeaderBefore(last, fee);
            $('#fees').append(feeHtml);
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
                feeRows += '<td>' + payment[fee.name] + '</td>';
            }
            var row = '<tr>';
            row += '<td>' + payment.order + '</td>';
            row += '<td>' + payment.date + '</td>';
            row += feeRows;
            row += '<td>' + payment.savings + '</td>';
            row += '<td>' + payment.payment + '</td>';
            row += '<td>' + payment.acct_balance + '</td>';
            row += '</tr>';
            body.append(row);
        }
    }

    function clearTableHeaders(table) {
        table.find('thead tr th.dymamic-added').remove();
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
        $('#total-fees').html(data.total_fees);
        $('#est-sett-dollars').html(data.total_sett);
        $('#total-debt').html(data.total_debt);
        $('#est-client-savings-with-no-fees').html(data.total_savings);
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
        $('#first-payment-date').show();
        $('#id_first_date').val(data.first_date);
        if (data.second_date) {
            $('#second-payment-date').show();
            $('#id_second_date').val(data.second_date);
        }
        else {
            $('#second-payment-date').hide();
            $('#id_second_date').val('');
        }
    }

    function refreshEnrollmentScreen(data, programLengthContainer, table, refreshAll) {
        var fees = data.fees;
        setDates(data);
        refreshTotals(data);
        generatePayments(data.payments, fees, table);
        if (refreshAll) {
            generateSelectorsAndAddTableHeaders(fees, table);
            setProgramLengthOptions(data.program_lengths);
            selectProgramLength(data.length_selected);
        }
        programLengthContainer.show();
    }

    function requestEnrollmentPlanInfo(sendExtraFields, refreshAll) {
        var planId = $('#id_enrollment_plan').val();
        var table = $('#payments-table');
        var programLengthContainer = $('#edit-program-length-container');
        if (refreshAll) {
            clearTableHeaders(table);
            clearTableBody(table);
            clearFeesDropdowns();
        }
        if (planId !== '') {
            var url = getEnrollmentPlanInfoUrl.replace('0', planId);
            var debtsIds = getDebtIds();
            var recurringDate = $('#id_start_date').val();
            url += '?start_date=' + recurringDate + '&debt_ids=' + debtsIds;
            if (sendExtraFields) {
                var firstDate = $('#id_first_date').val();
                var secondDate = $('#id_second_date').val();
                var monthsSelector = $('#id_program_length');
                var months = monthsSelector.val() != null ? monthsSelector.val() : '';
                url += '&first_date=' + firstDate + '&second_date=' + secondDate + '&months=' + months
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

    $('#id_second_date').change(function(e) {
        if (e.originalEvent) {
            requestEnrollmentPlanInfo(true, false);
        }
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
        requestEnrollmentPlanInfo(false, true);
    });
});