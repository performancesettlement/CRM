$(document).ready(function() {

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
                else {
                    $('#id_bank_name').val(null);
                    $('#id_state').val(null);
                    $('#id_city').val(null);
                    $('#id_address').val(null);
                    $('#id_phone').val(null);
                    $('#id_zip_code').val(null);
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

    showContents();
});