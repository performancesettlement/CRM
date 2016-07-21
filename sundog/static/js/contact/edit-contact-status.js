$(document).ready(function() {
    var defaultOption = $('<option></option>').html('--Select--');

    function generateStatusOptions(statusInfo) {
        if (statusInfo && statusInfo.length > 0) {
            var statusSelector = $('#id_status');
            for (var i = 0; i < statusInfo.length; i++) {
                var statusData = statusInfo[i];
                var newOption = $('<option></option>').attr('value', statusData['id']).html(statusData['name']);
                statusSelector.append(newOption);
            }
        }
        else {
            $('#stage-no-selector-message').hide();
            $('#status-selector').hide();
            $('#no-status-message').show().css('display', 'inline-block');
        }
    }

    $('#id_stage').change(function() {
        var newValue = $(this).val();
        var statusSelector = $('#id_status');
        statusSelector.find('option').remove();
        statusSelector.append(defaultOption);
        $('#no-status-message').hide();
        if (newValue) {
            $('#stage-selector-message').hide();
            $('#status-selector').show().css('display', 'inline-block');
            var formData = [
                {name: 'stage_id', value: parseInt(newValue)},
                {name: 'csrfmiddlewaretoken', value: csrf}
            ];
            $.post(getStageStatusesUrl, formData, function(response) {
                generateStatusOptions(response.statuses);
            });
        }
        else {
            $('#stage-selector-message').show().css('display', 'inline-block');
            $('#status-selector').hide();
        }
    });

    showErrorPopup(form_errors);
});
