$(document).ready(function() {
    var datatableWrapper = $('.dataTables_wrapper');
    datatableWrapper.addClass('m-t-md');
    var buttons = datatableWrapper.find('.dt-button.buttons-collection.buttons-colvis');
    buttons.removeClass('dt-button');
    buttons.addClass('btn btn-default m-r-md');
    datatableWrapper.find('.form-control.input-sm').removeClass('form-control input-sm');
    datatableWrapper.find('.clear-search').addClass('btn btn-default m-l-xs');

    $('body').on('click', '.buttons-collection.buttons-colvis.btn.btn-default.m-r-md', function() {
        var buttonContainer = $('.dt-button-collection');
        var buttons = buttonContainer.find('.dt-button.buttons-columnVisibility.active');
        buttons.removeClass('dt-button');
        buttons.addClass('btn btn-default m-b-xs col-xs-12');
    });
});
