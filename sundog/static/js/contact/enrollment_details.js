$(document).ready(function() {
    function postData(elem, callback) {
        var formSelector = '#' + elem.attr('id').replace('submit', 'form');
        var form = $(formSelector);
        var formData = form.serializeArray();
        $.post(form.attr('action'), formData, callback);
    }

    function toggleFields(form, showSelectors, hideSelectors, semaphoreClass, checkSemaphoreClass) {
        showSelectors.forEach(function(selector) {
            var container = form.find(selector);
            container.addClass(semaphoreClass);
            container.show();
        });
        hideSelectors.forEach(function(selector) {
            var container = form.find(selector);
            container.removeClass(semaphoreClass);
            if (!container.hasClass(checkSemaphoreClass)) {
                container.hide();
            }
        });
    }

    var TYPE_CLASS = 'type-toggle';
    var SUB_TYPE_CLASS = 'sub-type-toggle';

    function toggleTypeExtraFormFields(form, value) {
        var showSelectors = [];
        var hideSelectors = [];
        if (['Account Transfer'].indexOf(value) !== -1) {
            hideSelectors = ['.account-details', '.address', '.associated-payment', '.associated-settlement', '.paid-to'];
            showSelectors = ['.from-payee'];
        }
        else if (['Client Refund'].indexOf(value) !== -1) {
            hideSelectors = ['.address', '.from-payee', '.associated-payment', '.associated-settlement', '.paid-to'];
            showSelectors = ['.account-details'];
        }
        else if (['Retained Performance Fee'].indexOf(value) !== -1) {
            hideSelectors = ['.account-details', '.address', '.from-payee', '.associated-settlement'];
            showSelectors = ['.associated-payment', '.paid-to'];
        }
        else if (['Earned Performance Fee'].indexOf(value) !== -1) {
            hideSelectors = ['.account-details', '.address', '.from-payee', '.associated-payment'];
            showSelectors = ['.associated-settlement', '.paid-to'];
        }
        else {
            hideSelectors = ['.account-details', '.address', '.from-payee', '.associated-payment', '.associated-settlement', '.paid-to'];
        }
        toggleFields(form, showSelectors, hideSelectors, TYPE_CLASS, SUB_TYPE_CLASS);
    }

    function toggleSubTypeFromExtraFields(form, value) {
        var showSelectors = [];
        var hideSelectors = [];
        if (['bank_wire'].indexOf(value) !== -1) {
            hideSelectors = ['.from-payee', '.address', '.associated-payment', '.associated-settlement', '.paid-to'];
            showSelectors = ['.account-details'];
        }
        else if (['check', 'standard_check'].indexOf(value) !== -1) {
            hideSelectors = ['.account-details', '.from-payee', '.associated-payment', '.associated-settlement', '.paid-to'];
            showSelectors = ['.address'];
        }
        else {
            hideSelectors = ['.account-details', '.address', '.from-payee', '.associated-payment', '.associated-settlement', '.paid-to'];
        }
        toggleFields(form, showSelectors, hideSelectors, SUB_TYPE_CLASS, TYPE_CLASS);
    }

    $('#add-payment-submit').click(function(event) {
        event.preventDefault();
        postData($(this), function(response) {
            handleErrors(response);
            if (response.result == 'Ok') {
                refreshScreen();
            }
        });
    });

    $('#edit-payment-submit').click(function(event) {
        event.preventDefault();
        postData($(this), function(response) {
            handleErrors(response);
            if (response.result == 'Ok' && response.data) {
                var data = response.data;
                var row = $('tr#' + data.payment_id);
                var modal = $('#edit-payment');
                row.find('.active').prop('checked', data.active);
                row.find('.date').val(data.date);
                row.find('.type').val(data.type);
                row.find('.sub_type').val(data.sub_type);
                row.find('.memo').val(data.memo);
                row.find('.amount').val(data.amount);
                row.find('.enrollment').val(data.enrollment);
                row.find('.account_number').val(data.account_number);
                row.find('.routing_number').val(data.routing_number);
                row.find('.account_type').val(data.account_type);
                row.find('.associated_settlement').val(data.associated_settlement);
                row.find('.associated_payment').val(data.associated_payment);
                row.find('.address').val(data.address);
                row.find('.paid_to').val(data.paid_to);
                row.find('.payee').val(data.payee);
                modal.modal('close');
                showSuccessPopup('Payment updated.');
            }
        });
    });

    $('.edit-payment').click(function(event) {
        event.preventDefault();
        var modal = $('#edit-payment');
        var row = $(this).parent().parent();
        var paymentId = parseInt(row.attr('id'));
        var active = row.find('.active span').hasClass('green');
        var date = row.find('.date').html();
        var amount = row.find('.amount').attr('val');
        var type = row.find('.type').attr('val');
        var subType = row.find('.sub_type').html();
        var memo = row.find('.memo').attr('val');
        var accountNumber = row.find('.account_number').html();
        var routingNumber = row.find('.routing_number').html();
        var accountType = row.find('.account_type').html();
        var associatedSettlement = row.find('.associated_settlement').html();
        var associatedPayment = row.find('.associated_payment').html();
        var address = row.find('.address').html();
        var paidTo = row.find('.paid_to').html();
        var payee = row.find('.payee').html();
        var enrollment = row.find('.enrollment').html();
        modal.find('#payment_id').html(paymentId);
        modal.find('#id_payment_id').val(paymentId);
        modal.find('#id_active').prop('checked', active);
        modal.find('#id_date').val(date);
        modal.find('#id_type').val(type);
        modal.find('#id_sub_type').val(subType);
        modal.find('#id_memo').val(memo);
        modal.find('#id_amount').val(amount);
        modal.find('#id_enrollment').val(enrollment);
        modal.find('#id_account_number').val(accountNumber);
        modal.find('#id_routing_number').val(routingNumber);
        modal.find('#id_account_type').val(accountType);
        modal.find('#id_associated_settlement').val(associatedSettlement);
        modal.find('#id_associated_payment').val(associatedPayment);
        modal.find('#id_address').val(address);
        modal.find('#id_paid_to').val(paidTo);
        modal.find('#id_payee').val(payee);
        modal.modal('show');
    });

    var addPaymentForm = $('#add-payment-form');
    var editPaymentForm = $('#edit-payment-form');

    $('#edit-payment').on('hidden.bs.modal', function() {
        editPaymentForm.find('input, select').val('');
    });

    $('#add-payment').on('hidden.bs.modal', function() {
        addPaymentForm.find('input, select').val('');
    });

    addPaymentForm.find('#id_type').change(function() {
        var newVal = $(this).val();
        toggleTypeExtraFormFields(addPaymentForm, newVal);
    });

    addPaymentForm.find('#id_sub_type').change(function() {
        var newVal = $(this).val();
        toggleSubTypeFromExtraFields(addPaymentForm, newVal)
    });

    editPaymentForm.find('#id_type').change(function() {
        var newVal = $(this).val();
        toggleTypeExtraFormFields(editPaymentForm, newVal);
    });

    editPaymentForm.find('#id_sub_type').change(function() {
        var newVal = $(this).val();
        toggleSubTypeFromExtraFields(editPaymentForm, newVal)
    });
});