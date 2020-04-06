var apiUrl = "api";
var tmplCache = {};
var controller = new TheaterControl();
var idleMon = new IdleMonitor();
var queue = new Queue(controller);
var browser = new FileBrowser(controller);
var search = new Search(controller);
var graphicsCard = new GraphicsCard(controller);
var harbor = new Harbor(controller);
controller.queue = queue;

function formatTime(time) {
    var hour = Math.floor(time / 60);
    var minute = Math.floor(time) % 60;
    return hour + ":" + (minute < 10 ? "0" + minute : minute);
}

function templ(name) {
    var f;
    if (tmplCache[name]) {
        f = tmplCache[name];
    } else {
        tmplCache[name] = _.template($("#tpl-" + name).text());
        f = tmplCache[name];
    }
    return f;
}

$.fn.tooltipize = function() {
    $(this).find("[rel='tooltip']").tooltip({
        placement: 'bottom',
        trigger: 'hover',
    });

    return this;
};

$(document.body).tooltipize();

$("#working")
    .ajaxStart(function() { $(this).fadeIn(); })
    .ajaxStop(function() { $(this).fadeOut(); });

setInterval(function() {
    if (!idleMon.isIdle()) {
        queue.update();
    }
}, 5000);

queue.update();
browser.list(".");