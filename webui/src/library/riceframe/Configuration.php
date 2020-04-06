<?php
namespace riceframe;

class Configuration implements \ArrayAccess
{
    private $dir;
    private $config;
    
    public function __construct($dir) {
        $this->dir = $dir;
        $this->load();
    }
    
    private function load() {
        $data = file_get_contents("{$this->dir}/production.json");
        $this->config = json_decode($data, true);
    }
    
    public function get($path) {
        $parts = explode(".", $path);
        $node = $this->config;
        for ($i = 0; $i < count($parts); $i++) {
            $key = $parts[$i];
            if (isset($node[$key])) {
                $node = $node[$key];    
            } else {
                throw new \Exception("Missing configuration @ '" . $path . "'");
            }
        }
        return $node;
    }
    
    public function offsetExists($offset) {
        try {
            $this->get($offset);
            return true;
        } catch (\Exception $e) {
            return false;
        }
    }
    
    public function offsetGet($offset) {
        return $this->get($offset);
    }
    
    public function offsetSet($offset, $value) {
        throw new \Exception("Not supported");
    }
    
    public function offsetUnset($offset) {
        throw new \Exception("Not supported");
    }
}