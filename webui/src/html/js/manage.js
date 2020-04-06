function TheaterControl() {
    var $enqueueModal = $("#enqueue-modal");
    var $errorModal = $("#error-modal");
    var $uri = $('#uri');
    var $time = $('#time');
    var $gain = $('#gain');
    var $volume = $('#volume');
    var $text1 = $('#text1');
    var $text2 = $('#text2');
    
    var self = this;
    
    this.call = function(func, args, callback, hidden) {
        args.act = func;
        args.apiKey = apiKey;
        
        $.ajax({
            url: apiUrl,
            type: 'POST',
            cache: false,
            dataType: "json",
            data: args,
            global: !hidden,
            success: function(data) {
                if (data._error) {
                    self.showError(data._error);
                    return;
                }
                callback(data);
            }
        });
    };
    
    this.skip = function(qid, title) {
        this.call("skip", {qid: qid}, function(data) {
            this.queue.render(data.status);
        });
    }
    
    this.promptEnqueue = function(uri) {
        $uri.val(uri);
        $time.val("");
        $gain.val("");
        $volume.val("");
        $text1.val("");
        $text2.val("");
        $enqueueModal.modal('show');
    }
    
    this.enqueue = function(uri, time, gain, volume, text1, text2) {
        this.call("enqueue", {
            url: uri,
            time: time,
            gain: gain,
            volume: volume,
            text1: text1,
            text2: text2
        }, function(data) {
            self.queue.render(data.status);
        });
    }
    
    this.enqueueRaw = function(args) {
        this.call("enqueue", args, function(data) {
            self.queue.render(data.status);
        });
    }
    
    this.showError = function(text) {
        $errorModal.find(".alert").text(text);
        
        $errorModal.modal({
            show: true,
        });
    }

    $enqueueModal.modal({
        backdrop: 'static',
        show: false,
    }).on('shown', function(evt) {
        $uri.focus();
    });

    $('#enqueue-direct-url').on('click', function(evt) {
        self.promptEnqueue('');
        evt.preventDefault();
    });
    
    $enqueueModal.find("form").on("submit", function(evt) {
        self.enqueue($uri.val(), $time.val(), $gain.val(), $volume.val(), $text1.val(), $text2.val());
        $enqueueModal.modal('hide');
        evt.preventDefault();
    });
}

function IdleMonitor() {
    var secondsIdle = 0;
    
    this.isIdle = function() {
        return secondsIdle >= 60 * 15;
    };
    
    setInterval(function() { secondsIdle++; }, 1000);
        
    $(document.body).on("mousemove", function(event) {
        secondsIdle = 0;
    });
}

function Queue(controller) {
    var previouslyFilled = false;
    var $container = $("#queue");
    var $queue = $container.children("ul");
    var $empty = $container.children(".no-results");
    var $loading = $container.children(".loading");
        
    function renderRow(data) {
        var $row = $(templ("queue-entry")({result: data}));
        $row[0].qid = data.qid;
        $row.hide(); // Hide it because we're going to animate it
        var $skip = $row.find(".skip-button");
        
        $row.tooltipize();
        
        if (data.skippable) {
            $skip.on("click", function(event) {
                controller.skip(data.qid, data.name);
            });
        } else {
            $skip.remove();
        }
        
        return $row;
    }

    this.render = function(data) {
        $loading.hide();
        
        if (!data.current && data.queue.length == 0) {
            $empty.show();
            
            if (previouslyFilled != false) {
                previouslyFilled = false;
                $queue.children("li").slideUp(400, function() {
                    $(this).remove();
                });
            }
            
            return;
        } else {
            if (previouslyFilled != true) {
                previouslyFilled = true;
                $empty.hide();
            }
        }
        
        var existing = $queue.children("li");
        var j = 0;
        var foundCurrent = false;
        var firstRow = null;
        
        for (var i = 0; i < existing.length; i++) {
            if (j < data.queue.length && existing[i].qid == data.queue[j].qid) {
                $(existing[i]).removeClass("active");
                if (!firstRow)
                    firstRow = existing[i];
                j++;
            } else if (data.current && existing[i].qid == data.current.qid) {
                $(existing[i]).addClass("active");
                foundCurrent = true;
                
                if (firstRow) { // Move to first
                    $(existing[i]).remove().insertAfter($empty);
                }
                
                firstRow = existing[i];
            } else {
                var found = false;
                
                for (var k = j; k < data.queue.length; k++) {
                    if (existing[i].qid == data.queue[k].qid) {
                        found = true;
                        break;
                    }
                }
                
                if (found) {
                    for (; j < data.queue.length; j++) {
                        if (existing[i].qid == data.queue[j].qid) {
                            break;
                        } else {
                            var row = renderRow(data.queue[j]);
                            $(existing[i]).before(row);
                            row.fadeIn();
                            if (!firstRow)
                                firstRow = row[0];
                        }
                    }
                    
                    if (!firstRow)
                        firstRow = existing[i];
                } else {
                    $(existing[i]).slideUp(400, function() {
                        $(this).remove();
                    });
                }
            }
        }
        
        if (!foundCurrent && data.current) {
            var row = renderRow(data.current);
            $queue.prepend(row);
            row.addClass("active");
            row.fadeIn();
        }
        
        for (; j < data.queue.length; j++) {
            var row = renderRow(data.queue[j]);
            $queue.append(row);
            row.fadeIn();
        }
    }
        
    this.update = function() {
        var self = this;
        controller.call("status", {}, function(data) {
            self.render(data);
        }, true);
    }
}

function FileBrowser(controller) {
    var $browser = $("#local");
    var $list = $browser.children("ul.file-list");
    var $loading = $browser.children(".loading");
    var $empty = $browser.children(".no-results");
    var $parentDir = $browser.find(".up-dir");
    var $refresh = $browser.find(".refresh");
    var $breadcrumb = $browser.find(".breadcrumb");
    
    var self = this;
    var parentDir = null;
    var lastDir = null;
    
    $refresh.on("click", function(evt) {
        if (lastDir) {
            self.list(lastDir);
        }
        evt.preventDefault();
    });
    
    $parentDir.on("click", function(evt) {
        if (parentDir) {
            self.list(parentDir);
        }
        evt.preventDefault();
    });
    
    function createBedcrumb(text, path, active) {
        var li = $(document.createElement("li"));
        var a = $(document.createElement("a"));
        a.text(text);
        a.attr("href", "#");
        a.on("click", function(e) {
            self.list(path);
            e.preventDefault();
        });
        li.append(a);
        if (active) {
            li.addClass("active");
        } else {
            li.append((' <span class="divider">/</span>'));
        }
        return li;
    }
    
    this.list = function(path) {
        lastDir = path;
        $refresh.removeClass("disabled");
        
        $list.addClass("updating");
        
        controller.call("dir", {q: path}, function(data) {
            $loading.hide();
            $list.children().remove();
            
            // Build bedcrumbs
            $breadcrumb.children().remove();
            var parts = path.split("/");
            if (path == "." || path == "/") {
                parts = [];
            }
            $breadcrumb.append(createBedcrumb("Home", ".", parts.length == 0));
            for (var i = 0; i < parts.length; i++) {
                $breadcrumb.append(createBedcrumb(parts[i], parts.slice(0, i + 1).join("/"), parts.length - 1 == i));
            }
            
            if (data.results.length == 0) {
                $empty.slideDown();
            } else {
                $empty.hide();
                
                var fragment = $(document.createDocumentFragment());
                
                for (var i = 0; i < data.results.length; i++) {
                    var row = $(document.createElement("li"));
                    row.addClass(data.results[i].dir ? "dir" : "file");
                    var a = $(document.createElement("a"));
                    row.append(a);
                    a.text(data.results[i].name);
                    a.attr("href", "#");
                    
                    if (data.results[i].dir) {
                        (function(a, path) {
                            a.on("click", function(e) {
                                self.list(path);
                                e.preventDefault();
                            });
                        })(a, data.results[i].path);
                    } else {
                        (function(a, path) {
                            a.on("click", function(e) {
                                controller.promptEnqueue(path);
                                e.preventDefault();
                            });
                        })(a, data.results[i].path);
                    }
                    
                    fragment.append(row);
                }
                
                $list.append(fragment);
            }
            
            parentDir = data.parent;
            
            if (data.parent) {
                $parentDir.removeClass("disabled");
            } else {
                $parentDir.addClass("disabled");
            }
        
            $list.removeClass("updating");
        });
    }
}

function Search(controller) {
    var $browser = $("#web");
    var $list = $browser.children("ul.search-results");
    var $intro = $browser.children(".intro");
    var $empty = $browser.children(".no-results");
    var $refresh = $browser.find(".refresh");
    var $form = $browser.find("form");
    var $query = $("#query");
    
    var self = this;
    var lastQuery = null;
    
    $refresh.on("click", function(evt) {
        if (lastQuery) {
            self.search(lastQuery);
        }
        evt.preventDefault();
    });
    
    this.search = function(query) {
        lastQuery = query;
        
        $intro.hide();
        $refresh.removeClass("disabled");
        $list.addClass("updating");
        
        controller.call("search", {q: query}, function(data) {
            $list.children().remove();
            
            if (data.results.length == 0) {
                $empty.slideDown();
            } else {
                var fragment = $(document.createDocumentFragment());
                
                for (var i = 0; i < data.results.length; i++) {
                    var entry = $(templ("search-entry")({result: data.results[i]}));
                    (function(entry, url) {
                        entry.find(".enqueue").on("click", function() {
                            controller.promptEnqueue(url);
                        });
                        entry.find(".open").on("click", function() {
                            window.open(url, '', '');
                        });
                    })(entry, data.results[i].url);
                    fragment.append(entry);
                }
                
                $list.append(fragment);
            }
            
            $list.removeClass("updating");
        });
    }
    
    $form.on("submit", function(evt) {
        self.search($query.val());
        $query.select();
        evt.preventDefault();
    });
    
    $("#sources .nav-tabs a[href='#web']").on('shown', function(evt) {
        $query.focus();
    });
}

function GraphicsCard(controller) {
    var $pane = $("#graphics-card");
    var $form = $pane.find("form");
    var $title = $("#graphics-title");
    var $content = $("#graphics-content");
    var $rating = $("#graphics-rating");
    var $ratingContent = $("#graphics-rating-content");
    var $style = $("#graphics-style");
    var $music = $("#graphics-music");
    
    $form.on("submit", function(evt) {
        controller.enqueueRaw({type: 'graphics-card', title: $title.val(),
            content: $content.val(), rating: $rating.val(), ratingcontent: $ratingContent.val(),
            style: $style.val(), music: $music.val()});
        $title.select();
        evt.preventDefault();
    });
    
    $("#sources .nav-tabs a[href='#graphics-card']").on('shown', function(evt) {
        $title.focus();
    });
}

function Harbor(controller) {
    var $pane = $("#harbor");
    var $form = $pane.find("form");
    var $id = $("#harbor-id");
    
    $form.on("submit", function(evt) {
        controller.enqueueRaw({type: 'harbor', id: $id.val()});
        $id.select();
        evt.preventDefault();
    });
    
    $("#sources .nav-tabs a[href='#harbor']").on('shown', function(evt) {
        $id.focus();
    });
}