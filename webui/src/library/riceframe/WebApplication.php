<?php
namespace riceframe;

class WebApplication extends Application
{
    public function __construct() {
        parent::__construct();
        
        $this['request^'] = function($app) {
            return new Request();
        };
        
        $this['response^'] = function($app) {
            return new Response();
        };
    }
    
    public function request() {
        return $this['request'];
    }
    
    public function response() {
        return $this['response'];
    }
}