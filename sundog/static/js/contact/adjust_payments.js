$(document).ready(function() {
    $('.select-all').click(function() {
        var container = $(this).parent();
        var checkboxes = container.find('.select-checkbox');
        checkboxes.prop('checked', true);
    });

    $('.clear-all').click(function() {
        var container = $(this).parent();
        var checkboxes = container.find('.select-checkbox');
        checkboxes.prop('checked', false);
    });

    $('#save').click(function() {
        showConfirmationPopup(
            'Are you sure you want to make these changes. This action cannot be undone!',
            'Yes, save changes',
            function() {
                var forms = [$('#edit-debits-form'), $('#edit-settlements-form'), $('#edit-fees-form')];
                var formData = [];
                for (var i = 0; i < forms.length; i++) {
                    var form = forms[i];
                    form.find('.enable-checkbox:checked').each(function() {
                        var valueElem = form.find('#' + $(this).attr('id').replace('_checkbox', ''));
                        formData.push({name: valueElem.attr('name'), value: valueElem.val()})
                    });
                    var cancel = form.find('.cancel-checkbox');
                    var cancelName = cancel.attr('name');
                    formData.push({name: cancelName, value: cancel.prop('checked')});
                    var prefix = cancelName.split('-')[0];
                    var paymentIds = [];
                    form.find('.select-checkbox:checked').each(function() {
                        paymentIds.push($(this).parent().parent().attr('id').replace('payment-', ''));
                    });
                    if (paymentIds.length > 0) {
                        formData.push({name: prefix + '-ids', value: paymentIds});
                    }
                }
                if (formData.length > 0) {
                    formData.push({name: 'csrfmiddlewaretoken', value: csrfToken});
                    $.ajax({
                        url: adjustPaymentsUrl,
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
            },
            true
        );
    });
});