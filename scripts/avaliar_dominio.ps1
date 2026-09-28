$ErrorActionPreference = "Stop"
Set-Location (Split-Path $PSScriptRoot -Parent)

$stamp = Get-Date -Format "yyyy-MM-dd_HHmm"
$out = "docs/resultados/avaliacao_$stamp.txt"
New-Item -ItemType Directory -Force -Path "docs/resultados" | Out-Null

function Run($title, $cmd) {
    "`n===== $title =====" | Tee-Object -FilePath $out -Append
    Invoke-Expression $cmd 2>&1 | Tee-Object -FilePath $out -Append
}

Run "build" "docker compose up -d --build"
Start-Sleep -Seconds 15
Run "ready" "curl.exe -s http://localhost:8000/ready"
Run "plano de sincronizacao" "docker compose exec -T api ragtest-plan-ingestion-sync"
Run "sincronizacao" "docker compose exec -T api ragtest-sync-ingestion --apply"
Run "avaliacao dev" "docker compose exec -T api ragtest-evaluate-retrieval --dataset dominio-v2-dev --mode all"
Run "avaliacao holdout" "docker compose exec -T api ragtest-evaluate-retrieval --dataset dominio-v2-holdout --mode all"
Run "calibracao fora de escopo" "docker compose exec -T api ragtest-calibrate-scope --split dev"

"`nResultado salvo em $out"
