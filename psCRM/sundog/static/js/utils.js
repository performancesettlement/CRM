function showErrorToast(message){
    toastr.options = {
        "closeButton": true,
        "debug": false,
        "newestOnTop": false,
        "progressBar": true,
        "positionClass": "toast-bottom-center",
        "preventDuplicates": false,
        "onclick": null,
        "showDuration": "300",
        "hideDuration": "1000",
        "timeOut": "2000",
        "extendedTimeOut": "1000",
        "showEasing": "swing",
        "hideEasing": "linear",
        "showMethod": "fadeIn",
        "hideMethod": "fadeOut"
    };

    toastr["error"](message)
}

function showErrorPopup(error){
    if(error!=null){
        if(typeof error == "string"){
            swal("Error!", error, "error");
        }else{
            var errors = error;
            var errorText = "<div align='left' class='sweet-alert-body-scroll'>";
            for(var i=0; i<errors.length; i++){
                errorText += "<strong>&#187;</strong> " + errors[i] + "<br/>";
            }
            errorText += "</div>";
            swal({
                title: "Validation Error(s)",
                html: true,
                type: "error",
                text: errorText
            });
        }
    }
}
