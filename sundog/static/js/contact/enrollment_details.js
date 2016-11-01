$(document).ready(function() {
    function postData(elem, callback) {
        var formSelector = '#' + elem.attr('id').replace('submit', 'form');
        var form = $(formSelector);
        var formData = form.serializeArray();
        $.post(form.attr('action'), formData, callback);
    }

    $('#add-payment-submit').click(function(event) {
        event.preventDefault();
        postData($(this), function(response) {
            handleErrors(response);
            if (response.result) {
                refreshScreen();
            }
        });
    });

    $('#edit-payment-submit').click(function(event) {
        event.preventDefault();
        postData($(this), function(response) {
            handleErrors(response);
            if (response.result == 'Ok' && response.data) {
                showSuccessPopup('Payment updated.');
                var data = response.data;
                var row = $('tr#' + data.payment_id);
                var modal = $('#edit-payment');
                row.find('.active').prop('checked', data.active);
                row.find('.date').val(data.date);
                row.find('.type').val(data.type);
                row.find('.sub_type').val(data.sub_type);
                row.find('.memo').val(data.memo);
                row.find('.amount').val(data.amount);
                modal.modal('close')
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
        modal.find('#id_payment_id').val(paymentId);
        modal.find('#id_active').prop('checked', active);
        modal.find('#id_date').val(date);
        modal.find('#id_type').val(type);
        modal.find('#id_sub_type').val(subType);
        modal.find('#id_memo').val(memo);
        modal.find('#id_amount').val(amount);
        modal.modal('show');
    });

    $('#edit-payment').on('hidden.bs.modal', function() {
        $('#edit-payment-form').find('input, select').val('');
    });

    $('#add-payment').on('hidden.bs.modal', function() {
        $('#add-payment-form').find('input, select').val('');
    });
});