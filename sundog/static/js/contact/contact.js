$(document).ready(function() {
    showErrorPopup(errors);

    $('#template-chooser').change(function(){
        var value = $('#template-chooser').val();
        $('.form-template').hide();
        $('#' + value).show();
    });

    $('#id_company').change(function() {
        var assignedToSelector = $('#id_assigned_to');
        assignedToSelector.find("option[value!='']").remove();
        var companyId = $(this).val();
        if (companyId !== '') {
            var users = usersByCompany[companyId];
            for (var i = 0; i < users.length; i++) {
                var user = users[i];
                assignedToSelector.append('<option value="' + user.id + '">' + user.name + '</option>');
            }
        }
    });

    $('#contact-form').submit(function(event) {
        if (isEdit) {
            event.preventDefault();
            var form = $(this);
            var formData = form.serializeArray();
            $.ajax({
                url: form.attr('action'),
                data: formData,
                type: 'POST',
                success: function(response){
                    if (response.errors) {
                        showErrorPopup(response.errors);
                    }
                    if (response.result) {
                        showSuccessPopup('Contact successfully updated!');
                    }
                }
            });
        }
    });
});
