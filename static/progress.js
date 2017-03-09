$(document).ready(function() {
    $("form#specific-classes").submit(function(event){
        console.log("Specific form submitted.");
        connectGetProgress(event);
        return false;
    });

    $("#test").click(function(event) {
        console.log("Test clicked!");
        $(".modal-background").show();
        testProgress();
    });

    $("form#random-classes").submit(function(event) {
        console.log("Random form submitted - number of randos: " + $("#randos").val());
        connectGetProgress(event);
    });

    function testProgress() {
    var id = setInterval(prog, 100);
    function prog() {
    for (i=1; i < 101; i++) {
    if (i == 100) {
        clearInterval(id);
        console.log("Closing progress bar.");
        $(".modal-background").hide();
   } else {
       console.log("Updating progress bar: " + i + "Test message");
       $("progress#bar").val(i);
       $("#p_message").text("Test message #" + i);
        }
    }
    }
};

});

function connectGetProgress(event) {
    $(document).ready(function() {
        var socket = io.connect('http://' + document.domain + ':' + location.port);
        $(".modal-background").show();

        socket.on('connect', function() {
            console.log("Client connected!");
            socket.emit('testConnect', {data: 'Client connected!'});
        });

        socket.on('disconnect', function() {
            console.log("Client disconnected.");
            socket.emit('testDisconnect', {data: 'Client disconnected!'});
        });

        socket.on('progress', function(progress) {
           if (progress.value == 100) {
                console.log("Closing progress bar.");
                $(".modal-background").hide();
           } else {
               console.log("Updating progress bar: " + progress.value + progress.message);
               $("#bar").val(progress.value);
               $("#p_message").text(progress.message);
           }
        });
    });
};



/*socket.on('sendpdf', function(data, filename){
    var blob = new Blob([data], {type: 'application/pdf'});
    if (window.navigator.msSaveOrOpenBlob) {
        window.navigator.msSaveBlob(blob, filename);
    }
    else {
        var elem = $("body").append("<a>");
        elem.href = window.URL.createObjectURL(blob);
        elem.download = filename;
        elem.click();
        window.URL.revokeObjectURL(elem);
        $("body").remove(elem);
    }
});*/

