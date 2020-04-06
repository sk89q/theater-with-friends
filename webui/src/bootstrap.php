<?php
define("ROOT_PATH", dirname(__FILE__));

set_include_path(get_include_path() . PATH_SEPARATOR . ROOT_PATH . "/library");

require_once "autoloader.php";
require_once "phperrorhandler.php";

// Import
use \riceframe\Application;
use \riceframe\Configuration;

// Construct app
$app = Application::instance();

$app['config'] = new Configuration(ROOT_PATH . "/configs");
    
$app['twig^'] = function($app) {
    require_once "Twig/Autoloader.php";
    Twig_Autoloader::register();
    
    $loader = new Twig_Loader_Filesystem(ROOT_PATH . "/templates");
    return new Twig_Environment($loader, array(
        'cache' => false,
        'auto_reload' => true,
        'autoescape' => true,
    ));
};
