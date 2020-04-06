<?php
namespace riceframe;

class Application implements \ArrayAccess
{
    private static $instance;
    private $values = array();
    private $instances = array();
    
    public static function instance() {
        if (!self::$instance) {
            self::$instance = new WebApplication();
        }
        
        return self::$instance;
    }
    
    protected function __construct() {
    }
    
    public function set($key, $value, $singleton = false) {
        $this->values[$key] = $value;
        
        if ($singleton) {
            $this->instance[$key] = null;
        }
    }
    
    public function get($key) {
        if (isset($this->values[$key])) {
            $value = $this->values[$key];
        } else {
            throw new \Exception("Application does not have value identified by key '" . $key . "'");   
        }
        
        if (is_object($value) && ($value instanceof \Closure)) {
            if (isset($this->instances[$key])) {
                if ($this->instances[$key] === null) {
                    return ($this->instances[$key] = call_user_func_array($value, array(&$this)));
                } else {
                    return $this->instances[$key];
                }
            } else {
                return call_user_func_array($value, array(&$this));
            }
        } else {
            return $value;
        }
    }
    
    public function offsetExists($offset) {
        return isset($this->values[$offset]);
    }
    
    public function offsetGet($offset) {
        return $this->get($offset);
    }
    
    public function offsetSet($offset, $value) {
        $singleton = false;
        if ($offset[strlen($offset) - 1] == "^") {
            $offset = substr($offset, 0, strlen($offset) - 1);
            $singleton = true;
        }
        return $this->set($offset, $value, $singleton);
    }
    
    public function offsetUnset($offset) {
        throw new \Exception("Not supported");
    }
}