$(document).ready(function() {
    $("#refresh-btn").click(function() {
        $("#refresh-status").text("refreshing backend...");
            console.log("refreshing");
        // FIXME
        $.get('/_db_refresh', function(data,status) {
            $.get('/_db_state', function(data) {
                $("#refresh-status").text('last update: ' + data.state);
                $("#refresh-modal").modal("hide");
                location.reload();
            });
        });
    });
});
