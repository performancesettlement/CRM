$(document).ready(function() {
    showErrorPopup(errors);

    $('#template-chooser').change(function(){
        var value = $('#template-chooser').val();
        $('.form-template').hide();
        $('.' + value).show();
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

    $('#save-contact-form').click(function () {
        // Find form's invalid fields
        invalid_field = $('#contact-form').find(':invalid').first();
        closestTemplate = invalid_field.closest('.form-template');
        templateClasses = closestTemplate.attr("class");
        if (templateClasses) {
            templateClasses = templateClasses.toString().split(' ');
            // Display invalid field's template
            $('#template-chooser').val(templateClasses[0]);
            $('.form-template').hide();
            $('.' + templateClasses[0]).show();
            // Display invalid field's tab
            $('.tab-pane').removeClass('active');
            closestTabPane = invalid_field.closest('.tab-pane');
            closestTabPane.addClass('active');
            tabPaneName = closestTabPane.attr("id");
            $('#' + tabPaneName.substr(0, tabPaneName.length - 7) + 'tab').click();
        }
    });

    $('#contact-form').submit(function (event) {
        event.preventDefault();
        var form = $(this);
        var formData = form.serializeArray();
        $.ajax({
            url: form.attr('action'),
            data: formData,
            type: 'POST',
            success: function (response) {
                if (response.errors) {
                    showErrorPopup(response.errors);
                }
                if (response.result) {
                    if (response.remove_public === true) {
                        $('#id_public').parent().parent().remove();
                    }
                    redirect(contactsListUrl);
                    if (isEdit) {
                        showSuccessPopup('Contact successfully updated!');
                    } else {
                        showSuccessPopup('Contact successfully created!');
                    }
                }
            }
        });
    });

});
