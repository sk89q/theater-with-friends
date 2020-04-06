<?php
namespace riceframe;

class Response
{
    public function redirect($url) {
        if (preg_match("#^[^:]+://#", $url)) {
            header("Location: $url");
        } else {
            $host = $_SERVER['HTTP_HOST'];
            $uri = rtrim(dirname($_SERVER['PHP_SELF']), '/\\');
            header("Location: http://$host$uri/$url");
        }
        
        exit;
    }

    public function httpCode($code) {
        switch ($code) {
            case 400:
                header("HTTP/1.1 400 Bad Request");
            case 401:
                header("HTTP/1.1 401 Not Authorized");
            case 403:
                header("HTTP/1.1 403 Forbidden");
            case 404:
                header("HTTP/1.1 404 Not Found");
        }
    }

    public function header($key, $value) {
        header("$key: $value");
    }
}