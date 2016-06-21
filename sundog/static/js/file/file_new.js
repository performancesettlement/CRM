$(document).ready(function(){
    $(".chosen-select").chosen({width:"100%"});
    $("div.group-date").find("input").datepicker({
        keyboardNavigation: false,
        forceParse: false,
        autoclose: true
    });

    $('#add-client-form').submit(function(event) {
        event.preventDefault();
        var form = $(this);

        var formData = {
            'name': $('#id_name').val(),
            'identification': $('#id_identification').val(),
            'client_type': $('#id_client_type').val(),
            'email': $('#id_email').val(),
            'phone_number': $('#id_phone_number').val(),
            'mobile_number': $('#id_mobile_number').val(),
            'country': $('#id_country').val(),
            'state': $('#id_state').val(),
            'address': $('#id_address').val(),
            'city': $('#id_city').val(),
            'zip_code': $('#id_zip_code').val()
        };

        // process the form
        $.ajax({
            type        : 'POST',
            url         : form.attr('action'),
            data        : formData,
            dataType    : 'json'
        }).done(function(data) {

            // log data to the console so we can see
            //console.log(data);
            if(data.hasOwnProperty('error')){
                showErrorPopup(data.error);
            }else{
                if(data.hasOwnProperty("result")){
                    var id, name;
                    if(data.result.hasOwnProperty('client_id')){
                        id = data.result.client_id;
                    }
                    if(data.result.hasOwnProperty('name')){
                        name = data.result.name;
                    }

                    var selectOption = "<option value='" + id + "'>" + name + "</option>";
                    var select = $('#id_client');
                    select.append(selectOption);
                    select.val(id);
                    select.trigger("chosen:updated");
                    resetForm($("#add-client-form"));
                    $('#add-client-close-button').click();
                }

            }

        }).fail(function() {
            swal("Error!", "The server couldn't process your request.", "error");
        });
    });

    showErrorPopup(form_errors);
});
