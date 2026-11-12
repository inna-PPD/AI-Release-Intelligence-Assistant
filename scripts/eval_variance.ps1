# Розкид метрик evals між прогонами: N повторних прогонів rag-eval → evals/results/variance/runK/.
# Основні результати (rag_answers.jsonl, rag_metrics.*) після цього відновлюються — на них прив'язане калібрування судді.
param([int]$Runs = 2, [int]$StartAt = 2)

$ErrorActionPreference = "Stop"
$root = Split-Path $PSScriptRoot -Parent
$results = Join-Path $root "evals\results"
$backup = Join-Path $results "variance\_main_backup"
$files = "rag_answers.jsonl", "rag_metrics.json", "rag_metrics.md"

New-Item -ItemType Directory -Force $backup | Out-Null
foreach ($f in $files) { Copy-Item (Join-Path $results $f) $backup -Force }

$env:PYTHONIOENCODING = "utf-8"
for ($k = $StartAt; $k -lt $StartAt + $Runs; $k++) {
    Write-Output "=== run $k"
    & (Join-Path $root ".venv\Scripts\python.exe") (Join-Path $root "main.py") rag-eval 2>&1 | Select-String "faithfulness|refusal_accuracy" | ForEach-Object Line
    $dst = Join-Path $results "variance\run$k"
    New-Item -ItemType Directory -Force $dst | Out-Null
    foreach ($f in $files) { Copy-Item (Join-Path $results $f) $dst -Force }
}

foreach ($f in $files) { Copy-Item (Join-Path $backup $f) $results -Force }
Remove-Item $backup -Recurse -Force
Write-Output "done; main results restored"
