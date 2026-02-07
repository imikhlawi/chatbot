# LLM-Service testen (llama.cpp server)
# Voraussetzung: GGUF in storage/models/ (Projektroot), Container läuft.
# Bei 32B-Modell: Erst 5–15 Min warten, bis "load_tensors: done" in docker compose logs llm erscheint.

$uri = "http://127.0.0.1:8080/completion"
$json = '{"prompt":"Sag kurz Hallo","n_predict":40}'
$bodyBytes = [System.Text.Encoding]::UTF8.GetBytes($json)

# Optional: Warten bis Server bereit (kein 503 mehr), max 20 Min
$maxWait = 20 * 60
$step = 15
$waited = 0
while ($waited -lt $maxWait) {
    try {
        $response = Invoke-RestMethod -Uri $uri -Method Post -ContentType "application/json; charset=utf-8" -Body $bodyBytes -ErrorAction Stop
        Write-Host "OK (Modell bereit):"
        $response | ConvertTo-Json -Depth 5
        exit 0
    } catch {
        if ($_.Exception.Response.StatusCode -eq 503) {
            Write-Host "Modell lädt noch... ($waited s) Nächster Versuch in ${step}s."
            Start-Sleep -Seconds $step
            $waited += $step
        } else {
            throw
        }
    }
}
Write-Host "Timeout: Nach $maxWait s noch 503. Logs prüfen: docker compose logs llm"
