function updateCompleted(select){
    var status_id = $(select).val();

    $.get("/completed_by_status/", {status_id: status_id })
        .done(function( data ) {
            if(data.hasOwnProperty('result')) {
                var completed = data.result;
                $('#progress_bar_div').attr('style','width: '+completed+'%');
                var progressText = 'File completed in <strong>' + completed+'%</strong>';
                $("#progress_text").html(progressText);
            }
        });
}

$(document).ready(function(){

    Dropzone.options.uploadDocumentsForm = {
        previewTemplate: '<div class="dz-preview dz-file-preview">' +
        '<div class="dz-details">' +
        '<div class="dz-filename"><span data-dz-name></span></div>' +
        '<div class="dz-size" data-dz-size></div>' +
        '<img data-dz-thumbnail />' +
        '</div>' +
        '<div class="dz-progress"><span class="dz-upload" data-dz-uploadprogress></span></div>' +
        '<div class="dz-success-mark"><span>?</span></div>' +
        '<div class="dz-error-mark"><span>?</span></div>' +
        '<div class="dz-error-message"><span data-dz-errormessage></span></div>' +
        '<div class="dz-remove text-center">' +
        '<a  class="i-pointer btn btn-white btn-bitbucket" data-dz-remove=""><i class="i-pointer fa fa-trash"></i></a><a class="doc-download m-l i-pointer btn btn-white btn-bitbucket"><i class="i-pointer fa fa-download"></i></a>' +
        '</div></div>',
        success: function(file, response) {
            var id = response.document_id;
            file.serverId = id;
            var myDropzone = this;
            if (!( /\.(jpe?g|png|gif|bmp)$/i.test(file.name))) {
                myDropzone.emit("thumbnail", file, "/static/img/default_thumbnail.png");
            }
            myDropzone.emit("complete", file);

        },
        removedfile: function(file) {
            var fileArray = file.name.split(".");
            $.post("/delete-documents/" + file.serverId + "/");
            var _ref;
            return (_ref = file.previewElement) != null ? _ref.parentNode.removeChild(file.previewElement) : void 0;
        },
        // Dropzone settings
        init: function() {
            var myDropzone = this;
            if(document_list!=null) {
                for (var i=0; i<document_list.length; i++) {

                    var mockFile = {name: document_list[i].name, size: document_list[i].size, serverId: document_list[i].id};

                    // Call the default addedfile event handler
                    myDropzone.emit("addedfile", mockFile);

                    // And optionally show the thumbnail of the file:
                    if( /\.(jpe?g|png|gif|bmp)$/i.test(mockFile.name) ) {
                        myDropzone.emit("thumbnail", mockFile, document_list[i].url);
                    }else{
                        myDropzone.emit("thumbnail", mockFile, "/static/img/default_thumbnail.png");
                    }

                    // Make sure that there is no progress bar, etc...
                    myDropzone.emit("complete", mockFile);
                }

                // If you use the maxFiles option, make sure you adjust it to the correct amount:
                //var existingFileCount = document_list.length; // The number of files already uploaded
                //myDropzone.options.maxFiles = myDropzone.options.maxFiles - existingFileCount;

            }
        }

    };

    $(".chosen-select").chosen({width:"100%"});
    $("div.group-date").find("input").datepicker({
        keyboardNavigation: false,
        forceParse: false,
        autoclose: true
    });

    if(message!=null && message!=undefined){
        showErrorToast(message);
    }

    $('#upload-message-form').submit(function(event) {
        event.preventDefault();
        var form = $(this);

        var formData = {
            'message': $('textarea[name=message]').val(),
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
                if(data.hasOwnProperty('message')){
                    var time, message, name;
                    if(data.message.hasOwnProperty('time')){
                        time = data.message.time;
                    }
                    if(data.message.hasOwnProperty('user_full_name')){
                        name = data.message.user_full_name;
                    }
                    var input = $('textarea[name=message]');
                    message = input.val();

                    var tmplMarkup = $('#template-feed-element').html();
                    var compiledTmpl = tmplMarkup.replace(/__TIME__/g, time);
                    compiledTmpl = compiledTmpl.replace(/__FULL_NAME__/g, name);
                    compiledTmpl = compiledTmpl.replace(/__MESSAGE__/g, message);
                    $('.feed-activity-list').append(compiledTmpl);
                    input.val("");
                }

            }).fail(function() {
                showErrorToast("Error!, Your note didn't upload successfully.");
            });
    });

    $( ".participant-modal-button" ).click(function() {
        var aTag = $( this );

        var username = aTag.attr('data-username');
        var imgProfile = aTag.find(".img-circle");
        $('#pModalProfileImage').attr('src', imgProfile.attr('src'));
        $('#pModalFullname').html(imgProfile.attr('data-original-title'));
        $('#pModalUsername').html(username);
        var button = $('#pModalRemoveButton');
        if(button!=null && button!=undefined){
            var userId = aTag.attr('data-id');
            $("#user_id").val(userId);
            button.click(function(){
                $("#remove-participant-form").submit();
            })
        }

    });

    $("#add-participant-button").click(function(){
       setTimeout(function(){
           var search_field = $("#add-participant-form").find('li.search-field');
           search_field.css('width', '100%');
           search_field.find('input').css('width', '100%');
       }, 500);
    });

    $(document).on('click', '.doc-download', function(event) {
        event.preventDefault();
        var aTag = $( this );
        var preview = aTag.parent().parent();
        var document =  preview.find(".dz-filename span").html();
        window.location.href = "/media/" + document;
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
                    $('#add-client-close-button').click();
                }

            }

        }).fail(function() {
            swal("Error!", "The server couldn't process your request.", "error");
        });
    });

    showErrorPopup(form_errors);
});



