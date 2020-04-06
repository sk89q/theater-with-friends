<?php
namespace riceframe;

class GlobalsProxy implements \ArrayAccess
{
    private $data;
    
    public function __construct($data) {
        $this->data = &$data;
    }
    
    public function offsetSet($offset, $value) {
        throw new Exception("Cannot set");
    }
    
    public function offsetExists($offset) {
        return isset($this->data[$offset]);
    }
    
    public function offsetUnset($offset) {
        throw new Exception("Cannot unset");
    }
    
    public function offsetGet($offset) {
        return isset($this->data[$offset]) ? $this->data[$offset] : null;
    }
}

class Request
{
    public $get;
    public $post;
    
    public function __construct() {
        $this->get = new GlobalsProxy($_GET);
        $this->post = new GlobalsProxy($_POST);
    }

    public function getClientIp() {
        return isset($_SERVER["HTTP_CF_CONNECTING_IP"]) ? $_SERVER["HTTP_CF_CONNECTING_IP"] : $_SERVER["REMOTE_ADDR"];
    }

    public function getHttpUsername() {
        return isset($_SERVER['PHP_AUTH_USER']) ? $_SERVER['PHP_AUTH_USER'] : "";
    }

    public function getHttpPassword() {
        return isset($_SERVER['PHP_AUTH_PW']) ? $_SERVER['PHP_AUTH_PW'] : "";
    }
}