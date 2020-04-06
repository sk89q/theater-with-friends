<?php
require_once "../bootstrap.php";

// Import
use \riceframe\Application;

\theater\ControlPanel::authenticate();

// Initialize
$app = Application::instance();
$twig = $app['twig'];
$request = $app['request'];
$response = $app['response'];
$conf = $app['config'];

$csrfKey = \theater\Util::getCsrf();

echo $twig->render('manage.html', array('csrfKey' => $csrfKey));