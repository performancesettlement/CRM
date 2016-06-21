$(document).ready(function() {

    var $inputImage = $("#id_avatar");
    if (window.FileReader) {
        $inputImage.change(function() {
            var fileReader = new FileReader(),
                files = this.files,
                file;

            if (!files.length) {
                return;
            }

            file = files[0];

            if ((/^image\/\w+$/.test(file.type)) && (file.size<1048576)) {
                fileReader.readAsDataURL(file);
                fileReader.onload = function () {
                    $("#preview_image").attr("src",this.result);
                    $("#preview_div").show();
                    $("#submit_button").prop('disabled', false);
                };
            } else {
                $(this).val("");
                toastr.options = {
                    "closeButton": true,
                    "debug": false,
                    "newestOnTop": false,
                    "progressBar": true,
                    "positionClass": "toast-top-center",
                    "preventDuplicates": false,
                    "onclick": null,
                    "showDuration": "300",
                    "hideDuration": "1000",
                    "timeOut": "3000",
                    "extendedTimeOut": "1000",
                    "showEasing": "swing",
                    "hideEasing": "linear",
                    "showMethod": "fadeIn",
                    "hideMethod": "fadeOut"
                }

                toastr["error"]("Oops, We couldn't upload your picture, please choose a valid file!")
            }
        });
    } else {
        $inputImage.removeClass("hide");
    }
});