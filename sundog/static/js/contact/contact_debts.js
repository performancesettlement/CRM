$(document).ready(function() {

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

    function calculateTotal(debtId, selector, isAdd) {
        var amountToAdd = parseFloat($('#' + debtId + '-' + selector).attr('value').replace('$', '').replace(',', ''));
        if (amountToAdd > 0) {
            var amountElem = $('#' + selector);
            var amount = parseFloat(amountElem.html().replace('$', '').replace(',', ''));
            if (!isAdd) {
                amountToAdd = -amountToAdd;
            }
            amountElem.html('$' + (amount + amountToAdd).toFixed(2).replace(/(\d)(?=(\d{3})+\.)/g, '$1,'));
        }
    }

    $('.enrolled-checkbox').change(function(){
        var checkbox = $(this);
        var debtId = parseInt(checkbox.attr('id').replace('-enrolled-checkbox', ''));
        var formData = [
            {name: 'csrfmiddlewaretoken', value: csrfToken},
            {name: 'debt_id', value: debtId},
            {name: 'enrolled', value: checkbox.prop('checked')}
        ];
        $.post(editDebtEnrolledUrl, formData, function(response) {
            if (response.result == 'Ok') {
                var isAdd = checkbox.prop('checked');
                calculateTotal(debtId, 'original-debt-amount', isAdd);
                calculateTotal(debtId, 'current-debt-amount', isAdd);
                calculateTotal(debtId, 'current-payment', isAdd);
                showSuccessToast('Enrolled updated successfully.');
            }
        });
    })
});
