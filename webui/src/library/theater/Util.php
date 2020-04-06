<?php
namespace theater;

class Util
{
    public static function getCsrf() {
        session_start();
        
        if (!isset($_SESSION['csrfKey'])) {
            $fp = @fopen('/dev/urandom', 'rb');
            if ($fp !== FALSE) {
                $_SESSION['csrfKey'] = sha1(fread($fp, 64));
                @fclose($fp);
            } else {
                $_SESSION['csrfKey'] = sha1(mt_rand(0, 99999999999999));
            }
        }
        
        return $_SESSION['csrfKey'];
    }
}