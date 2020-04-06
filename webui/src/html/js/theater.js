function centerObject(el) {
    var moveIt = function () {
        var winWidth = $(window).width();
        var winHeight = $(window).height();
        el
            .css("position","absolute")
            .css("left", ((winWidth / 2) - (el.width() / 2)) + "px")
            .css("top", ((winHeight / 2) - (el.height() / 2)) + "px");
    }; 
    $(window).resize(moveIt);
    moveIt();
};

$(document).ready(function() {
    var image = new Image();
    image.src = "/images/working_black.gif";
    
    var $splash = $("#splash");
    var $theater = $("#theater");
    var $streams = $("#streams");
    var $error = $("#error");
    var $underlay = $("#underlay");

    function canPlay() {
        return jwplayer.utils.flashVersion() >= 10;
    }

    function embedPlayer(url) {
        jwplayer("player").setup({
            file: url,
            width: "100%",
            height: "100%",
            autostart: true,
            repeat: true
        });
    }
    
    function embedChat() {
        swfobject.embedSWF("http://skcrafttheater.chatango.com/group", 
            "chat", "100%", "100%", "9.0.0", "js/expressInstall.swf", {
            cid: "1333780738384",
            a: "000000",
            b: "100",
            c: "999999",
            d: "848484",
            e: "000000",
            g: "999999",
            h: "333333", // Input text
            j: "FFFFFF", // Input BG
            k: "000000", // Date text
            l: "000000", // Border
            m: "000000",
            n: "CCCCCC",
            t: "0",
            v: "0",
            w: "0",
            ab: "1"
        }, {
            allowscriptaccess: "never",
            allownetworking: "all",
            allowfullscreen: "true",
            bgcolor: "000000"
        }, {});
    }

    if (canPlay()) {
        $("#splash .btn").popover({
            title: "How's your Internet?",
            trigger: "hover",
            placement: "bottom"
        }).on("click", function(event) {
            var $this = $(this);
            var url = $this.attr("data-stream-url");
            $splash.fadeOut();
            $underlay.fadeIn(function() {
                $theater.show();
                embedPlayer(url);
            });
        });
        
        $streams.fadeIn(500);

        $streams.find("button").click();
        
        //embedChat();
    } else {
        $error.find("span").text("Sorry, your browser is not supported. This stream requires Adobe Flash 10 or greater.");
        $error.show();
    }
    
    centerObject($splash);
});