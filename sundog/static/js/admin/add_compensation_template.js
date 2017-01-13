$(document).ready(function() {
    function toggleButton(buttonSelector, condition){
        if (condition) {
            $(buttonSelector).show();
        }
        else {
            $(buttonSelector).hide();
        }
    }

    $('#add-fee').click(function() {
        var lastFee = $('#fee-' + formCount).clone();
        lastFee.find('input[type="hidden"]').remove();
        lastFee = lastFee.html();
        var nextCount = formCount + 1;
        var newFee = lastFee
            .replace('<span>' + formCount + '</span>', '<span>' + nextCount + '</span>')
            .replace(formCount + '-', nextCount + '-')
            .replace(formCount + '-type', nextCount + '-type')
            .replace('id_' + formCount + '-payee', 'id_' + nextCount + '-payee')
            .replace(formCount + '-payee', nextCount + '-payee')
            .replace('id_' + formCount + '-fee_amount', 'id_' + nextCount + '-fee_amount')
            .replace(formCount + '-fee_amount', nextCount + '-fee_amount');
        newFee = '<div id="fee-' + nextCount + '" class="col-xs-4 no-padding-sides m-t-md">' + newFee + '</div>';
        $('#fees').append(newFee);
        formCount = nextCount;
        toggleButton('#remove-last-fee', formCount > 1);
    });

    $('#remove-last-fee').click(function() {
        if (formCount > 1) {
            $('#fee-' + formCount).remove();
            formCount--;
            toggleButton('#remove-last-fee', formCount > 1);
        }
    });

    $('#comp-temp-chooser').change(function() {
        var newVal = $(this).val();
        if (newVal == '') {
            redirect(addCompensationTemplateUrl);
        } else {
            redirect(editCompensationTemplateUrl.replace('0', newVal));
        }
    });

    showErrorPopup(formErrors);
});