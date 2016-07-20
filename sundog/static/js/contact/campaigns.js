$(document).ready(function() {
    function hideForms() {
        var forms = $('#forms');
        forms.children().each(function(index) {
            $(this).hide();
        });
    }

    function cleanForms() {
        var forms = $('#forms');
        forms.children().each(function(index) {
            var form = $(this);
            form.find('input').val('');
            form.find('select').val('');
        });
    }

    hideForms();

    $('.edit-campaign').click(function(event) {
        event.preventDefault();
        var campaignId = parseInt($(this).attr('id'));
        var campaignActive = $('#' + campaignId + '-active').attr('value');
        var campaignTitle = $('#' + campaignId + '-title').attr('value');
        var campaignStartDate = $('#' + campaignId + '-start_date').attr('value');
        var campaignEndDate = $('#' + campaignId + '-end_date').attr('value');
        var campaignSource = $('#' + campaignId + '-source').attr('value');
        var campaignMediaType = $('#' + campaignId + '-media_type').attr('value');
        var campaignPriority = $('#' + campaignId + '-priority').attr('value');
        var campaignCost = parseFloat($('#' + campaignId + '-cost').attr('value'));
        var campaignPurchaseAmount = parseFloat($('#' + campaignId + '-purchase_amount').attr('value'));
        var form = $('#edit-campaign-form');
        form.find('#id_campaign_id').val(campaignId);
        form.find('#id_active').val(campaignActive);
        form.find('#id_title').val(campaignTitle);
        form.find('#id_start_date').val(campaignStartDate);
        form.find('#id_end_date').val(campaignEndDate);
        form.find('#id_source').val(campaignSource);
        form.find('#id_media_type').val(campaignMediaType);
        form.find('#id_priority').val(campaignPriority);
        form.find('#id_cost').val(campaignCost);
        form.find('#id_purchase_amount').val(campaignPurchaseAmount);
        hideForms();
        $('#edit-campaign').show();
    });

    $('.cancel').click(function(event) {
        hideForms();
        cleanForms();
    });

    $('#add-campaign-button').click(function() {
        hideForms();
        $('#add-campaign').show();
    });

    $('#add-source-button').click(function() {
        hideForms();
        $('#add-source').show();
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
