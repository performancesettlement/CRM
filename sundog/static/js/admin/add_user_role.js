$(document).ready(function() {
    function getSelectedPermissions(formData) {
        var selectedPermissions = [];
        var selectedInputs = $('#permissions-container').find('input:checked');
        selectedInputs.each(function() {
            selectedPermissions.push($(this).attr('id'));
        });
        formData.push({name: 'ids', value: selectedPermissions})
    }

    $('.select-all').click(function() {
        var section = $(this).parents('.section-container');
        section.find('.permission-checkbox, .section-checkbox').prop('checked', true)
    });

    $('.select-none').click(function() {
        var section = $(this).parents('.section-container');
        section.find('.permission-checkbox, .section-checkbox').prop('checked', false)
    });

    $('#select-role').change(function() {
        var val = $(this).val();
        if (val !== '') {
            redirect(editRoleUrl.replace('0', val));
        }
        else {
            redirect(addRoleUrl);
        }
    });

    $('#save-role').click(function() {
        var form = $('#add-role-form');
        var formData = form.serializeArray();
        getSelectedPermissions(formData);
        $.ajax({
            url: form.attr('action'),
            data: formData,
            type: 'POST',
            success: function(response) {
                if (response.errors) {
                    showErrorPopup(response.errors);
                }
                if (response.result === 'Ok') {
                    $('#select-role').append('<option value="' + response.id + '">' + response.name + '</option>');
                    $('select').val('');
                    var name = $('#id_name');
                    var nameContainer = name.parent();
                    name.remove();
                    nameContainer.append('<input class="col-xs-6" id="id_name" maxlength="80" name="name" required="" type="text">');
                    $('input[type="checkbox"]').prop('checked', false);
                    showSuccessPopup('User Role successfully created!');
                }
            }
        });
    });
});