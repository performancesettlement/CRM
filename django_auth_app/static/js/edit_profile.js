$(document).ready(function(){

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
    $('.zip-code').mask('00000-000');

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

var autocomplete;
var componentForm = {
    street_number: 'short_name',
    route: 'long_name',
    locality: 'long_name',
    administrative_area_level_1: 'short_name',
    postal_code: 'short_name'
};
var componentFormConv = {
    street_number: 'id_address',
    route: 'id_address',
    locality: 'id_city',
    administrative_area_level_1: 'id_state',
    postal_code: 'id_zip_code'
};

function initAutocomplete() {
    // Create the autocomplete object, restricting the search to geographical
    // location types.
    autocomplete = new google.maps.places.Autocomplete(
        /** @type {!HTMLInputElement} */(document.getElementById('id_address')),
        {types: ['geocode']});

    // When the user selects an address from the dropdown, populate the address
    // fields in the form.
    autocomplete.addListener('place_changed', fillInAddress);
}

function fillInAddress() {
    // Get the place details from the autocomplete object.
    var place = autocomplete.getPlace();

    for (var component in componentFormConv) {
        document.getElementById(componentFormConv[component]).value = '';
    }

    // Get each component of the address from the place details
    // and fill the corresponding field on the form.
    for (var i = 0; i < place.address_components.length; i++) {
        var addressType = place.address_components[i].types[0];
        if (componentFormConv[addressType]) {
            var val = place.address_components[i][componentForm[addressType]];
            if(document.getElementById(componentFormConv[addressType]).value.length>0){
                document.getElementById(componentFormConv[addressType]).value+=" ";
            }
            document.getElementById(componentFormConv[addressType]).value += val;
        }
    }
}
