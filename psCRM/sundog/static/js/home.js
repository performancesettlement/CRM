var monthNames = [
    "January", "February", "March",
    "April", "May", "June", "July",
    "August", "September", "October",
    "November", "December"
];

function validate_search(){
    var url = window.location.href;
    var q="", startdate="", enddate="", sort_field="",sort_class="", radio_field="";
    var index = url.indexOf("?");
    if(index>=0){
        var query = url.substring(index+1);
        var params = query.split("&");
        for(var i=0;i<params.length; i++){
            var strq = params[i].split("=");
            if(strq[0]=="q"){
                q=decodeURIComponent(strq[1]).replace("+"," ");
            }
            if(strq[0]=="created_start"){
                startdate=decodeURIComponent(strq[1]);
            }
            if(strq[0]=="created_end"){
                enddate=decodeURIComponent(strq[1]);
            }
            if(strq[0]=="sort_column"){
                sort_field=decodeURIComponent(strq[1]).replace("+","_");
            }
            if(strq[0]=="sort_asc"){
                sort_class=decodeURIComponent(strq[1]);
            }
            if(strq[0]=="radio_field"){
                radio_field=decodeURIComponent(strq[1]);
            }
        }
    }
    $("input[name=q]").val(q);
    $("input[name=created_start]").val(startdate);
    $("input[name=created_end]").val(enddate);
    if(sort_field.length){
        //var sort_column = sort_array[1].replace("+", "_");
        var header = $("#th_"+sort_field);
        header.removeClass();
        header.addClass("sorting");
        header.addClass(sort_class);
    }

    if(radio_field.length && radio_field=="1"){
        $("label[for=id_radio_field_1]").addClass("active");
        $('#id_radio_field_1').prop("checked", true);
    }else{
        $("label[for=id_radio_field_0]").addClass("active");
        $('#id_radio_field_0').prop("checked", true);
    }
}

function updateSearch(){
    $('input[name=page]').val("");
    $('#search-form').submit();
}

$(document).ready(function(){

    $("#side-menu").find("li").removeClass('active');
    $('#menu_home').addClass('active');

    validate_search();

    $('#dataTable').find("th.sorting").click(function () {

        var sort = $(this);
        var sortClass="";
        if(sort.hasClass("sorting_desc")){
            sortClass = "sorting_asc";
        }else{
            sortClass = "sorting_desc";
        }
        $('input[name=sort_asc]').val(sortClass);
        $('input[name=sort_column]').val(sort.html());
        $('input[name=page]').val("");
        $('#search-form').submit();
    });

    $( ".move-page" ).click(function() {
        var button = $( this );
        var page = button.html();
        $('input[name=page]').val(page);
        $('#search-form').submit();
    });

    $( ".prev-page" ).click(function() {
        var input = $('input[name=page]');
        var prevPage = parseInt(input.val()) - 1;
        input.val(prevPage);
        $('#search-form').submit();
    });

    $( "label[for=id_radio_field_0]" ).click(function() {
        $('#id_radio_field_0').prop("checked", true);
        $('input[name=page]').val("");
        $('#search-form').submit();
    });

    $( "label[for=id_radio_field_1]" ).click(function() {
        $('#id_radio_field_1').prop("checked", true);
        $('input[name=page]').val("");
        $('#search-form').submit();
    });

    $( ".next-page" ).click(function() {
        var input = $('input[name=page]');
        var nextPage = parseInt(input.val()) + 1;
        input.val(nextPage);
        $('#search-form').submit();
    });

    $('#created_range').find('.input-daterange').datepicker({
        keyboardNavigation: false,
        forceParse: false,
        autoclose: true
    });
    if(chart_data!=null){
        Morris.Area({
            element: 'morris-area-chart',
            data: chart_data,
            xkey: "day",
            xLabelFormat: function(date) {
                return (date.getMonth()+1) + '/' + date.getDate() + '/' + date.getFullYear();
            },
            //behaveLikeLine: true,
            ykeys: chart_status_names,
            labels: chart_status_names,
            xLabels: "day",
            pointSize: 2,
            hideHover: 'auto',
            resize: true,
            // lineColors: ['#87d6c6', '#54cdb4','#1ab394'],
            lineWidth:2,
            dateFormat: function(date) {
                var d = new Date(date);
                return (d.getMonth()+1) + '/' + d.getDate() + '/' + d.getFullYear();
            }
        });
    }else{
        $('#morris-area-chart-container').hide();
    }
});





