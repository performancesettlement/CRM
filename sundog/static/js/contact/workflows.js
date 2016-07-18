

$(document).ready(function() {
    var stagesSelector = '#stages';
    var statusesSelector = '.statuses';
    var stagesChanged = false;
    var statusesChanged = false;

    function setSortable(selector) {
        var statuses = $(selector);
        statuses.sortable();
        statuses.disableSelection();
    }

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
            form.find('#id_color').val('#FFFFFF');
            form.find('select').val('');
        });
    }

    function getStageType() {
        return $('#type-chooser').val();
    }

    function hideByType() {
        var forms = $('#stages');
        var type = getStageType();
        forms.children().each(function(index) {
            var stage = $(this);
            if (!stage.hasClass(type)) {
                stage.hide();
            }
            else {
                stage.show();
            }
        });
    }

    function sendToTypeScreen() {
        window.location.replace(workflow_url + '?type=' + getStageType());
    }

    hideForms();
    hideByType();
    $('[name="type"]').val(getStageType());

    $('#type-chooser').change(function() {
        sendToTypeScreen();
    });

    $('.edit-status').click(function(event) {
        event.preventDefault();
        var status = $(this);
        var status_name = status.attr('name');
        var status_stage = parseInt(status.attr('stage'));
        var status_color = status.attr('color');
        var status_id = parseInt(status.attr('id'));
        var form = $('#edit-status-form');
        form.find('#id_name').val(status_name);
        form.find('#id_stage').val(status_stage);
        form.find('#id_color').val(status_color);
        form.find('#id_status_id').val(status_id);
        hideForms();
        $('#edit-status').show();
    });

    $('.edit-stage').click(function(event) {
        event.preventDefault();
        var stage = $(this);
        var stage_name = stage.attr('name');
        var stage_id = parseInt(stage.attr('id'));
        var form = $('#edit-stage-form');
        form.find('#id_name').val(stage_name);
        form.find('#id_stage_id').val(stage_id);
        hideForms();
        $('#edit-stage').show();
    });

    $('.cancel').click(function(event) {
        hideForms();
        cleanForms();
    });

    $('#add-stage-button').click(function() {
        hideForms();
        $('#add-stage').show();
    });

    $('#add-status-button').click(function() {
        hideForms();
        $('#add-status').show();
    });

    $('.form').submit(function(event) {
        event.preventDefault();
        var form = $(this);
        var formData = form.serializeArray();
        formData.push({name: 'stage_type', value: getStageType()});
        $.post(form.attr('action'), formData, function(response) {
            if (response.errors) {
                showErrorPopup(form_errors);
            }
            if (response.result) {
                sendToTypeScreen();
            }
        });
    });

    setSortable(stagesSelector);
    setSortable(statusesSelector);

    $(stagesSelector).on('sortchange', function(event, ui) {
        stagesChanged = true;
    });

    $(stagesSelector).on('sortbeforestop', function(event, ui) {
        if (stagesChanged) {
            var stages = $(this);
            var stagesOrder = [];
            var stagesArray = stages.children();
            for (var stageIndex = 0; stageIndex < stagesArray.length; stageIndex++) {
                var stageRowId = stagesArray[stageIndex].id;
                if (stageRowId && stageRowId.startsWith('stage-')) {
                    var stageId = stageRowId.replace('stage-', '');
                    stagesOrder.push(stageId);
                }
            }
            if (stagesOrder) {
                var formData = {};
                for (var i in stagesOrder) {
                    formData[i] = stagesOrder[i];
                }
                $.post(update_stage_order_url, formData, function(response) {});
            }
            stagesChanged = false;
        }
    });

    $(statusesSelector).on('sortchange', function(event, ui) {
        statusesChanged = true;
    });

    $(statusesSelector).on('sortbeforestop', function(event, ui) {
        if (statusesChanged) {
            var statuses = $(this);
            var stageId = statuses.attr('id').replace('stage-', '').replace('-statuses', '');
            var statusesOrder = [];
            var statusesArray = statuses.children();
            for (var statusesIndex = 0; statusesIndex < statusesArray.length; statusesIndex++) {
                var statusRowId = statusesArray[statusesIndex].id;
                if (statusRowId && statusRowId.startsWith('status-')) {
                    var statusId = statusRowId.replace('status-', '');
                    statusesOrder.push(statusId);
                }
            }
            if (statusesOrder) {
                var formData = {stageId: stageId};
                for (var i in statusesOrder) {
                    formData[i] = statusesOrder[i];
                }
                $.post(update_status_order_url, formData, function(response) {});
            }
            statusesChanged = false;
        }
    });
});