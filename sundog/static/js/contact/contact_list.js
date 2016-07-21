$(document).ready(function() {
    $('.move-page').click(function() {
        var button = $(this);
        var page = button.html();
        $('input[name=page]').val(page);
        $('#search-form').submit();
    });

    $('.prev-page').click(function() {
        var input = $('input[name="page"]');
        var prevPage = parseInt(input.val()) - 1;
        input.val(prevPage);
        $('#search-form').submit();
    });

    $('.next-page').click(function() {
        var input = $('input[name="page"]');
        var nextPage = parseInt(input.val()) + 1;
        input.val(nextPage);
        $('#search-form').submit();
    });
});