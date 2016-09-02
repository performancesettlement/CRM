$(document).ready(function() {

    var emailMessage = CKEDITOR.replace('message');

    var files = [];

    function showContents() {
        $('.dashboard-button').each(function() {
            var elem = $(this);
            var content = $('#' + elem.attr('id').replace('-btn', ''));
            if (elem.hasClass('btn-primary')) {
                content.show();
            } else if (elem.hasClass('btn-default')) {
                content.hide();
            }
        });
    }

    function deactivateButtons() {
        $('.dashboard-button').each(function() {
            $(this).removeClass('btn-primary');
            $(this).addClass('btn-default');
        });
    }

    function activateButton(elem) {
        $(elem).removeClass('btn-default');
        $(elem).addClass('btn-primary');
    }

    $('.dashboard-button').click(function(event) {
        event.preventDefault();
        deactivateButtons();
        activateButton(this);
        showContents();
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

    $('#id_routing_number').change(function() {
        $.ajax({
            type: "GET",
            dataType: "jsonp",
            async: true,
            url: "https://www.routingnumbers.info/api/data.json",
            data: {
                rn: $(this).val()
            },
            success: function(response) {
                if (response.code == 200) {
                    $('#id_bank_name').val(response.customer_name);
                    $('#id_state').val(response.state);
                    $('#id_city').val(response.city);
                    $('#id_address').val(response.address);
                    $('#id_phone').val(response.telephone);
                    $('#id_zip_code').val(response.zip);
                }
                else if (response.code === 400) {
                    showErrorPopup(response.message);
                }
                else if (response.code === 404) {
                    showErrorPopup('This routing number was not found.');
                }
            },
            error: function(data) {
                alert(data.statusText);
            }
        });
    });

    $('.submit').click(function() {
        var formSelector = '#' + $(this).attr('id').replace('submit', 'form');
        var form = $(formSelector);
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

    function switchRadios(elem) {
        $('.radio-file-type').prop('checked', false);
        $(elem).prop('checked', true);
    }

    function switchRadiosData(id) {
        $('.radio-file-data').hide();
        $('#' + id + '-data').show();
    }

    function drawFiles() {
        var filesContainer = $('#files');
        filesContainer.html('');
        for (var i = 0; i < files.length; i++) {
            filesContainer.append(
                '<div>' +
                    '<div class="inline m-r-md">' + files[i].name + '</div>' +
                    '<a class="remove-file">' +
                        '<span id="file-' + i + '" class="glyphicon glyphicon-remove" style="color: darkred;"></span>' +
                    '</a>' +
                '</div>'
            );
        }
    }

    $('#files').on('click', '.remove-file', function(event) {
        event.preventDefault();
        var elem = $(this);
        var index = parseInt($(elem.children()[0]).attr('id').replace('file-', ''));
        files.splice(index, 1);
        drawFiles();
    });

    $('.radio-file-type').change(function() {
        var elem = $(this);
        var id = elem.attr('id');
        switchRadios(elem);
        switchRadiosData(id);
    });

    $('#id_file_upload').change(function() {
        var elem = $(this);
        files.push(elem.prop('files')[0]);
        elem.val('');
        drawFiles();
    });

    $('#email-submit').click(function(event) {
        event.preventDefault();
        var form = $('#add-email-form');
        var formBaseData = form.serializeArray();
        var messageData = emailMessage.getData();
        var formData = new FormData();
        for (var dataIndex = 0; dataIndex < formBaseData.length; dataIndex++) {
            var elem = formBaseData[dataIndex];
            formData.append(elem.name, elem.value);
        }
        formData.set('message', messageData);
        for (var fileIndex = 0; fileIndex < files.length; fileIndex++) {
            formData.set('file-' + fileIndex, files[fileIndex])
        }

        $.ajax({
            url: form.attr('action'),
            data: formData,
            processData: false,
            contentType: false,
            type: 'POST',
            success: function(response){
                if (response.errors) {
                    showErrorPopup(response.errors);
                }
                if (response.result) {
                    refreshScreen();
                }
            }
        });
    });

    $('#upload-file-form').find('#id_content').change(function() {
        var form = $('#upload-file-form');
        var fileName = $(this).val();
        var mimeType = $(this).prop('files')[0].type;
        form.find('#id_name').val(fileName);
        form.find('#id_mime_type').val(mimeType);
    });

    $('#upload-file').on('hidden.bs.modal', function() {
        $('#upload-file-form').find('input, select, textarea').val('');
    });

    $('#upload-file-submit').click(function(event) {
        event.preventDefault();
        var form = $('#upload-file-form');
        var formBaseData = form.serializeArray();
        var formData = new FormData();
        for (var dataIndex = 0; dataIndex < formBaseData.length; dataIndex++) {
            var elem = formBaseData[dataIndex];
            formData.append(elem.name, elem.value);
        }
        formData.set('content', form.find('#id_content').prop('files')[0]);

        $.ajax({
            url: form.attr('action'),
            data: formData,
            processData: false,
            contentType: false,
            type: 'POST',
            success: function(response){
                if (response.errors) {
                    showErrorPopup(response.errors);
                }
                if (response.result) {
                    refreshScreen();
                }
            }
        });
    });

    $('.uploaded-doc-delete').click(function(event){
        event.preventDefault();
        showConfirmationPopup('You will not be able to recover this file!');
        var button = $(this);
        var url = button.prop('href');
        showConfirmationPopup(
            'You will not be able to recover this file!',
            function() {
                $.ajax({
                    url: url,
                    beforeSend: function (xhr) {
                        xhr.setRequestHeader("X-CSRFToken", csrfToken);
                    },
                    type: 'DELETE',
                    success: function (response) {
                        if (response && response.result === 'Ok') {
                            var row = button.parent().parent();
                            var tableRows = row.parent();
                            row.remove();
                            if (tableRows.children().length == 1) {
                                tableRows.find('.empty-table').show();
                            }
                            showSuccessPopup('Uploaded file has been successfully deleted.');
                        }
                        else {
                            showErrorPopup('An error occurred deleting the file.');
                        }
                    }
                });
            }
        );
    });

    $('#delete-contact').click(function(event){
        event.preventDefault();
        var url = $(this).prop('href');
        showConfirmationPopup(
            'You will not be able to recover this data!',
            function() {
                $.ajax({
                    url: url,
                    beforeSend: function(xhr) {
                        xhr.setRequestHeader("X-CSRFToken", csrfToken);
                    },
                    type: 'DELETE',
                    success: function(response) {
                        if (response && response.result == 'Ok') {
                            var location = $('#list-contacts-link').prop('href');
                            redirect(location);
                        }
                        else {
                            showErrorPopup('An error occurred deleting the contact.');
                        }
                    }
                });
            }
        );
    });

    showContents();
    switchRadiosData('local');
});