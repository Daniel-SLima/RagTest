$ErrorActionPreference = "Continue"
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
Set-Location (Split-Path $PSScriptRoot -Parent)

$stamp = Get-Date -Format "yyyy-MM-dd_HHmm"
$out = "docs/resultados/avaliacao_$stamp.txt"
New-Item -ItemType Directory -Force -Path "docs/resultados" | Out-Null

function Log($text) {
    Write-Host $text
    Add-Content -Path $out -Value $text -Encoding UTF8
}

function Run($title, $cmd) {
    Log "`n===== $title ====="
    cmd /c "chcp 65001>NUL & $cmd 2>&1" | ForEach-Object { Log "$_" }
    if ($LASTEXITCODE -ne 0) {
        Log "FALHOU: '$title' terminou com codigo $LASTEXITCODE"
        Log "Resultado parcial salvo em $out"
        exit 1
    }
}

Run "build" "docker compose up -d --build"

Log "`n===== aguardando a API ====="
$ready = $false
for ($i = 0; $i -lt 60; $i++) {
    $status = cmd /c "curl.exe -s -o NUL -w %{http_code} http://localhost:8000/health 2>NUL"
    if ($status -eq "200") { $ready = $true; break }
    Start-Sleep -Seconds 3
}
if (-not $ready) {
    Log "FALHOU: a API nao respondeu em /health depois de 3 minutos"
    exit 1
}
Log "API pronta"

Run "ready" "curl.exe -s http://localhost:8000/ready"
Run "plano de sincronizacao" "docker compose exec -T api ragtest-plan-ingestion-sync"
Run "sincronizacao" "docker compose exec -T api ragtest-sync-ingestion --apply"
Run "avaliacao dev" "docker compose exec -T api ragtest-evaluate-retrieval --dataset dominio-v2-dev --mode all"
Run "avaliacao holdout v3 (congelado)" "docker compose exec -T api ragtest-evaluate-retrieval --dataset dominio-v3-holdout --mode all"
Run "criterio de aprovacao (dev, hybrid)" "docker compose exec -T api ragtest-evaluate-retrieval --dataset dominio-v2-dev --mode hybrid --min-pass-rate 0.9 --min-mrr 0.75"
Run "calibracao fora de escopo" "docker compose exec -T api ragtest-calibrate-scope --split dev"

Log "`nConcluido. Resultado salvo em $out"
