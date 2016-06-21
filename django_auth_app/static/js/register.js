$(document).ready(function(){
    var tz = jstz.determine();
    //console.log(tz.name());
    $('#id_timezone').val(tz.name());
    $("#id_username").on('blur keyup', function() {
        var username = $(this);
        if(username.val().length){
            username.val(username.val().toLowerCase())
        }
    });
    $('#id_birthday').datepicker({
        startView: 2,
        keyboardNavigation: false,
        forceParse: false,
        autoclose: true
    });
    $("#id_birthday").change(function() {
        var birthdayDate = $("#id_birthday").val();
        var todayDate = new Date();
        var yesterdayDate = todayDate.setDate(todayDate.getDate() - 1);
        if (Date.parse(birthdayDate) > yesterdayDate) {
            $("#id_birthday").val("");
        }
    });
    $('.chosen-select').chosen({width:"100%"});
    $('.phone-us').mask('(000) 000-0000');
    showErrorPopup(form_errors);
});

function updateAreasOfInterest(selector){
    var state_id = $(selector).val();

    $.get("/areas_by_state/", {state_id: state_id })
        .done(function( data ) {
            var options = '<option value="" selected="selected">Select the area of interest...</option>';
            if(data.hasOwnProperty('results') && data.results.length>0) {
                for (var i=0; i<data.results.length; i++) {
                    options += '<option value="' + data.results[i].id + '">'
                        + data.results[i].name + '</option>';
                }
            }
            $("#id_area_of_interest").html(options);
        });
}

function updateCommunitiesOfInterest(selector){
    var area_id = $(selector).val();

    $.get("/communities_by_area/", {area_id: area_id })
        .done(function( data ) {
            var options = '';
            if(data.hasOwnProperty('results') && data.results.length>0) {
                for (var i=0; i<data.results.length; i++) {
                    options += '<option value="' + data.results[i].id + '">'
                        + data.results[i].name + '</option>';
                }
            }
            var select = $("#id_communities_of_interest");
            select.html(options);
            select.trigger("chosen:updated");
        });
}
