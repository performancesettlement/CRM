$(document).ready(function(){

    $("#side-menu").find("li").removeClass('active');
    $('#menu_import').addClass('active');
    $('#submenu_client_import').addClass('active');

    Dropzone.options.uploadImportForm = {
        maxFiles:1,
        acceptedFiles: '.xls, .xlsx',
        accept: function(file, done) {
            var myDropzone = this;
            var form = $('#upload-import-form');
            var formData = new FormData(form[0]);
            var inputFile = $("input[type=file]");
            formData.append("file", inputFile[0].files[0], file.name);
            $.ajax({
                url: '/client/import/check/',
                type: 'POST',
                data: formData,
                success: function (data) {
                   // console.log(data);
                    if(data.hasOwnProperty("result") && data.result=="OK"){
                        done();
                    }else if (data.hasOwnProperty("warning")){
                        swal({   title: "Warning!",
                            text: data.warning,
                            type: "warning",
                            showCancelButton: true,
                            confirmButtonColor: "#DD6B55",
                            confirmButtonText: "Yes, upload anyways!",
                            closeOnConfirm: false }, function(isConfirm){
                            if (isConfirm) {
                                done();
                            } else {
                                done("Cancelled");
                                myDropzone.removeFile(file);
                            }
                        });
                    }else if (data.hasOwnProperty("error")){
                        swal("Error!", data.error, "error");
                        done(data.error);
                    }else{
                        done("The server couldn't process your request.");
                    }
                },
                enctype: 'multipart/form-data',
                cache: false,
                contentType: false,
                processData: false
            });
        },
        addRemoveLinks: true,
        success: function(file, response) {
            this.removeFile(file);
            if(response.hasOwnProperty("result")){
                if(typeof response.result == "string" && response.result=="OK"){
                    swal("Success!", "The file was imported successfully.", "success");
                }else{
                    showErrorPopup(response.result);
                }
            }else{
                swal("Error!", "The server couldn't process your request.", "error");
            }
        }

    };

});



