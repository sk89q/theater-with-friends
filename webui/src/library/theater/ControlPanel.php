<?php
namespace theater;

class ControlPanel
{
    public static function authenticate() {
        $app = \riceframe\Application::instance();
        $conf = $app['config'];
        $accounts = $conf['control-panel.accounts'];
        
        $username = $app->request()->getHttpUsername();
        $password = $app->request()->getHttpPassword();
        
        if (!isset($accounts[$username]) || $password != $accounts[$username]) {
            $app->response()->httpCode(401);
            $app->response()->header("WWW-Authenticate", 'Basic realm="Control Panel"');
            echo "Invalid user/password!";
            exit;
        }
    }
}