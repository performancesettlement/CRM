$(document).ready(function() {
    $('#list-chooser').change(function() {
        var selector = $(this);
        window.location.replace(contacts_list_url + '?selected_list=' + selector.val());
    });
});
