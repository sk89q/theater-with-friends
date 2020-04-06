<?php
require_once "../bootstrap.php";

// Import
use \riceframe\Application;

// Initialize
$app = Application::instance();
$twig = $app['twig'];
$request = $app['request'];
$response = $app['response'];
$conf = $app['config'];

if ($request->get['type'] == 'play') {
    $id = $request->post['id'];
    
    if ($id != $conf['relay-id'] && $id != $conf['active-stream.id']) {
        $response->httpCode(403);
        echo "No access";
        exit;
    }
    
    echo "Good";
    exit;
} else if ($request->get['type'] == 'publish') {
    $key = $request->post['key'];
    
    if (!in_array($key, $conf['harbor.keys']) ){
        $response->httpCode(403);
        echo "Invalid credential!";
        exit;
    }
    
    echo "Good";
    exit;
} else {
    $response->httpCode(403);
    echo "???";
    exit;
}