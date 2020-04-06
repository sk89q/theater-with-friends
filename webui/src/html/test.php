<?php
require_once "../library/Google/autoload.php";

$q = "test";

$results = array();

$client = new Google_Client();
$client->setDeveloperKey("AIzaSyDTmcqj_03f3YfTADSMJNxAg7psFwtEiiM");

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
    $thumbnail = $searchResult['snippet']['thumbnails']['medium'];
    
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