$(document).ready(function() {
    if (roleId !== '') {
        $('#id_groups').val(roleId);
    }
    $('#id_shared_with_all').change(function() {
        var sharedUserData = $('#id_shared_user_data');
        if ($(this).prop('checked')) {
            sharedUserData.find('option:selected').prop('selected', false);
            sharedUserData.attr('disabled','disabled');
            sharedUserData.hide();
        }
        else {
            sharedUserData.removeAttr('disabled');
            sharedUserData.show();
        }
    });

    $('#edit-user-form').submit(function(event) {
        event.preventDefault();
        var form = $(this);
        var formData = form.serializeArray();
        $.ajax({
            url: form.attr('action'),
            data: formData,
            type: 'POST',
            success: function(response) {
                if (response.errors) {
                    showErrorPopup(response.errors);
                }
                if (response.result === 'Ok') {
                    $('#id_password').val('');
                    $('#id_confirm_password').val('');
                    showSuccessPopup('User successfully updated!');
                }
            }
        });
    });

    $('#suspend-user').click(function(event) {
        event.preventDefault();
        showConfirmationPopup('This user will not be able to login into the system.', 'Yes, suspend', function(){
            $.ajax({
                url: suspendUserUrl,
                type: 'POST',
                success: function(response) {
                    if (response.result === 'Ok') {
                        $('#suspend-user').parent().hide();
                        $('#activate-user').parent().show();
                        showSuccessPopup('User successfully suspended!');
                    }
                }
            });
        }, false);
    });

    $('#activate-user').click(function(event) {
        event.preventDefault();
        showConfirmationPopup('This user will be able to login into the system.', 'Yes, activate', function() {
            $.ajax({
                url: activateUserUrl,
                type: 'POST',
                success: function(response) {
                    if (response.result === 'Ok') {
                        $('#activate-user').parent().hide();
                        $('#suspend-user').parent().show();
                        showSuccessPopup('User successfully activated!');
                    }
                }
            });
        }, false);
    });
});