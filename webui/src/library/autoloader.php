<?php
set_include_path(get_include_path() . PATH_SEPARATOR . dirname(__FILE__));

spl_autoload_register(function($name) {
    $path = dirname(__FILE__) . "/" . str_replace("\\", "/", $name) . ".php";
    
    if (file_exists($path)) {
        require_once $path;
        return;
    }
    
    $path = dirname(__FILE__) . "/" . str_replace("_", "/", $name) . ".php";
    
    if (file_exists($path)) {
        require_once $path;
        return;
    }
    
});