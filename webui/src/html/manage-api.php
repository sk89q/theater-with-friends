<?php
require_once "../bootstrap.php";
require_once "Google/autoload.php";

// Import
use \riceframe\Application;
//use \JsonRpcClient;

\theater\ControlPanel::authenticate();

// Initialize
$app = Application::instance();
$twig = $app['twig'];
$request = $app['request'];
$response = $app['response'];
$conf = $app['config'];

header("Content-Type: text/plain");

try {
    /*if (\theater\Util::getCsrf() != $request->post['apiKey']) {
        throw new Exception("Please refresh the page.");
    }*/

    // Initialize APIs
    $api = new JsonRpcClient($conf['control-panel.api-server']);
    $yt = new Zend_Gdata_YouTube();
    $yt->setMajorProtocolVersion(2);

    $act = $request->post['act'];

    function buildQueueEntry($item) {
        return array(
            'qid' => $item->qid,
            'name' => $item->name,
            'filters' => $item->filters,
            'skippable' => canSkip($item),
        );
    }

    function buildQueueOutput($api) {
        $out = array();
        $queue = $api->queue();
        
        $out['queue'] = array();
        foreach ($queue->queue as $item) {
            $out['queue'][] = buildQueueEntry($item);
        }
        
        $out['current'] = $queue->current != null ? buildQueueEntry($queue->current) : null;
        
        return $out;
    }

    function canSkip($item) {
        return true;
    }

    switch ($act) {
        case "skip":
            $qid = $request->post['qid'];
            
            $queue = $api->queue();
            $skipItem = null;
            
            if ($queue->current && $queue->current->qid == $qid) {
                if (canSkip($queue->current)) {
                    $skipItem = $queue->current;
                }
            }
            
            if (!$skipItem) {
                foreach ($queue->queue as $item) {
                    if ($item->qid == $qid && canSkip($item)) {
                        $skipItem = $item;
                        break;
                    }
                }
            }
            
            if (!$skipItem) {
                throw new Exception("Failed to find the track that you want to skip, or you cannot skip that track.");
            }
            
            $api->skip($skipItem->qid);
            
            echo json_encode(array(
                'status' => buildQueueOutput($api),
            ));
            
            break;
        
        case "status":
            echo json_encode(buildQueueOutput($api));
            
            break;
        
        case "enqueue":
            $inputType = $request->post['type'];
            $url = $request->post['url'];
            $time = trim($request->post['time']);
            $gain = trim($request->post['gain']);
            $volume = trim($request->post['volume']);
            $text1 = $request->post['text1'];
            $text2 = $request->post['text2'];
            
            if ($inputType == "graphics-card") {
                $type = "graphics";
                $title = $request->post['title'];
                $content = $request->post['content'];
                $rating = $request->post['rating'];
                $rating_content = $request->post['ratingcontent'];
                $style = $request->post['style'];
                $music = $request->post['music'];
                
                $data = array(
                    'texts' => array(
                        'title' => $title,
                        'content' => $content,
                        'rating' => $rating,
                        'rating-content' => $rating_content,
                    ),
                    'style' => $style,
                    'audio' => empty($music) ? null : $music,
                );
            } else if ($inputType == "harbor") {
                $type = "harbor";
                $id = $request->post['id'];
                
                if (!preg_match("#^[A-Za-z0-9\\-_]{1,20}$#", $id)) {
                    throw new Exception("Invalid harbor ID");
                }
                
                $data = array(
                    'id' => $id,
                );
            } else {
                if (preg_match("#https?://#i", $url, $m)) {
                    $type = "web";
                    $data = array('url' => $url);
                } else {
                    $type = "file";
                    $data = array('path' => $url);
                }
            }
            
            $filters = array();
            
            if (!empty($text1) && !empty($text2)) {
                $filters[] = array(
                    'type' => 'corner-overlay',
                    'data' => array(
                        'text1' => $text1,
                        'text2' => $text2,
                    ),
                );
            }
            
            if (preg_match("#^(?:[0-9]{1,4}:)?[0-9]{1,2}:[0-9]{1,2}|[0-9]{1,4}$#", $time)) {
                $filters[] = array(
                    'type' => 'skip-time',
                    'data' => array(
                        'time' => $time,
                    ),
                );
            }
            
            if (preg_match("#^\\-([0-9]+)$#", $volume)) {
                $filters[] = array(
                    'type' => 'volume-boost',
                    'data' => array(
                        'gain' => intval($gain),
                        'volume' => intval($volume),
                    ),
                );
            }
            
            try {
                $api->enqueue($type, $data, $filters, array());
            } catch (Exception $e) {
                throw new Exception("Failed to queue $url: {$e->getMessage()}");
            }
            
            echo json_encode(array(
                'status' => buildQueueOutput($api),
            ));
            
            break;
        
        case "dir":
            $q = $request->post['q'];
            
            if (empty($q)) {
                throw new Exception("No query entered.");
            }
            
            $results = array();
            
            $data = $api->dir($q);
             
            foreach ($data->entries as $entry) {
                $results[] = array(
                    'name' => basename($entry->path),
                    'path' => $entry->path,
                    'dir' => $entry->dir,
                );
            }
            
            echo json_encode(array(
                'results' => $results,
                'parent' => $data->parent,
            ));
            
            break;
        
        case "search":
            $q = $request->post['q'];
            
            if (empty($q)) {
                throw new Exception("No query entered.");
            }
            
            $results = array();
            
            $client = new Google_Client();
            $client->setDeveloperKey("FIXME");

            $youtube = new Google_Service_YouTube($client);

            $searchResponse = $youtube->search->listSearch('id,snippet', array(
                'q' => $q,
                'safeSearch' => 'none',
                'regionCode' => 'CA',
                'maxResults' => 20,
                'type' => 'video',
            ));
             
            foreach ($searchResponse['items'] as $searchResult) {
                $id = $searchResult['id']['videoId'];
                $title = $searchResult['snippet']['title'];
                $desc = $searchResult['snippet']['description'];
                $thumbnail = $searchResult['snippet']['thumbnails']['medium']['url'];
                
                if (strlen($desc) > 100) {
                    $desc = trim(substr($desc, 0, 100)) . "...";
                }
                
                $results[] = array(
                    'id' => $id,
                    'url' => 'http://www.youtube.com/watch?v=' . $id,
                    'title' => $searchResult['snippet']['title'],
                    'desc' => $desc,
                    'duration' => "?",
                    'tn' => $thumbnail,
                );
            }
            
            echo json_encode(array(
                'results' => $results,
            ));
            
            break;
        
        default:
            header("HTTP/1.1 400 Bad Request");
    }
} catch (Exception $e) {
    echo json_encode(array(
        '_error' => $e->getMessage(),
    ));
}