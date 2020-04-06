<?php
function __default_error_handler($errlevel, $errstr, $errfile, $errline, $errcontext)
{
    if(($errlevel & error_reporting()) == 0) {
        return;
    }
    
    $error_names = array(E_WARNING => "Warning",
                         E_NOTICE => "Notice",
                         E_USER_ERROR => "Error",
                         E_USER_WARNING => "Error",
                         E_USER_NOTICE => "Notice",
                         E_STRICT => "Strict Notice",
                         E_RECOVERABLE_ERROR => "Error");
    
    $errlevelname = $error_names[$errlevel];
    
    $errstr = preg_replace("# \(include_path='[^']*'\)#", "", $errstr);
    $errstr = preg_replace("#<a #", '<a style="color:#0000FF;text-decoration:underline" ', $errstr);

    echo '<br /><div style="background:#FFFFFF;color:#000000;font-family:\'Bitstream Vera Sans Mono\',\'Lucida Console\',monospace;font-size:8pt;border:1px solid red;padding:3px;margin:0;position:relative;z-index:999999999;text-align:left">'."\n";
    echo sprintf("<strong>PHP %s</strong>: %s [%s:%d]<br />\n",
                 $errlevelname,
                 htmlspecialchars(strip_tags($errstr)),
                 basename($errfile),
                 $errline);
    echo '<div style="background:#EFEFEF;color:#000000;margin:3px -3px -3px -3px;padding:3px">';
    __dump_backtrace();
    echo "</div>";
    echo "</div>";
}

function __default_exception_handler($exception)
{    
    $errstr = $exception->getMessage() ? get_class($exception).": ".$exception->getMessage() : get_class($exception);
    
    $errstr = preg_replace("#<a #", '<a style="color:#0000FF;text-decoration:underline" ', $errstr);
    
    echo '<br /><div style="background:#FFFFFF;color:#000000;font-family:\'Bitstream Vera Sans Mono\',\'Lucida Console\',monospace;font-size:8pt;border:1px solid red;padding:3px;margin:0;position:relative;z-index:999999999;text-align:left">'."\n";
    echo sprintf("<strong>PHP %s</strong>: %s [%s:%d]<br />\n",
                 "Uncaught exception",
                 htmlspecialchars(strip_tags($errstr)),
                 basename($exception->getFile()),
                 $exception->getLine());
    echo '<div style="background:#EFEFEF;color:#000000;margin:3px -3px -3px -3px;padding:3px">';
    __dump_backtrace($exception->getTrace());
    echo "</div>";
    echo "</div>";
}

function __dump_backtrace_args($args)
{
    $list = array();
    
    if(!is_array($args)) {
        return "";
       }
    
    foreach ($args as $arg) {
        $list[] = gettype($arg);
    }
    
    return implode(",", $list);
}

function __dump_backtrace($trace = null)
{
    if (!$trace) {
        $trace = debug_backtrace();
    }
    
    $i = 0;
    foreach ($trace as $item) {
        if($item['function'] == "__dump_backtrace") continue;
        if($item['function'] == "__default_error_handler") continue;
        
        echo sprintf("&nbsp; at <strong>%s</strong>(%s) [%s:%d]<br />\n",
                     $item['class'].$item['type'].$item['function'],
                     __dump_backtrace_args($item['args']),
                     basename($item['file']),
                     $item['line']);
        
        $i++;
    }
}

function __dump_backtrace_text()
{
    $trace = debug_backtrace();
    
    $i = 0;
    foreach ($trace as $item) {
        if($item['function'] == "__dump_backtrace_text") continue;
        if($item['function'] == "__default_error_handler") continue;
        
        echo sprintf("  at %s(%s) [%s:%d]\n",
                     $item['class'].$item['type'].$item['function'],
                     __dump_backtrace_args($item['args']),
                     basename($item['file']),
                     $item['line']);
        
        $i++;
    }
}

set_error_handler('__default_error_handler');
set_exception_handler('__default_exception_handler');
?>