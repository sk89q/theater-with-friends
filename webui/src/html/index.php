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

if (($id = trim($request->get['id'])) != "") {
    if ($id == $conf['active-stream.id']) {
        $streams = array();
        
        foreach ($conf['active-stream.streams'] as $s) {
            $streams[] = array(
                'name' => $s['name'],
                'bandwidth' => $s['bandwidth'],
                'id' => $s['id'],
                'url' => $s['url'],
                'file' => str_replace("%id%", $id, $s['file']),
            );
        }
        
        echo $twig->render('index.html', array('streams' => $streams));
    } else {
        echo $twig->render('no_id.html', array('error' => true));
    }
} else {
    echo $twig->render('no_id.html', array());
}
