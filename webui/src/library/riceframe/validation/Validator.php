<?php
namespace Ricecake\validation;

class Validator {
    public $errors = array();
    
    public function hasErrors() {
        return count($this->errors) > 0;
    }

    public function checkNonBlank($value, $msg) {
        $value = trim($value);
        
        if ($value == "") {
            $this->errors[] = $msg;
            return null;
        }
        
        return $value;
    }

    public function checkRegex($value, $regex, $msg) {
        if (!preg_match($regex, $value)) {
            $this->errors[] = $msg;
            return null;
        }
        
        return $value;
    }

    public function checkEmail($value, $msg) {
        $value = trim($value);
        
        if (!preg_match("/^[^@]+@[^@]+\\.[^\\.@]+$/", $value)) {
            $this->errors[] = $msg;
            return null;
        }
        
        return $value;
    }
    
    public function checkInt($value, $min = null, $max = null, $msg) {
        $value = trim($value);
        
        if (!preg_match("/^\\-?[0-9]+$/", $value)) {
            $this->errors[] = $msg;
            return null;
        }
        
        $value = intval($value);
        
        if ($min != null) {
            if ($value < $min) {
                $this->errors[] = $msg;
                return null;
            }
        }
        
        if ($max != null) {
            if ($value > $max) {
                $this->errors[] = $msg;
                return null;
            }
        }
        
        return $value;
    }
    
    public function checkFloat($value, $min = null, $max = null, $msg) {
        $value = trim($value);
        
        if (!preg_match("/^\\-?[0-9]+(?:\\.[0-9]*)?$/", $value)) {
            $this->errors[] = $msg;
            return null;
        }
        
        $value = floatval($value);
        
        if ($min != null) {
            if ($value < $min) {
                $this->errors[] = $msg;
                return null;
            }
        }
        
        if ($max != null) {
            if ($value > $max) {
                $this->errors[] = $msg;
                return null;
            }
        }
        
        return $value;
    }
}