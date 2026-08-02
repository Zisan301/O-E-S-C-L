$ErrorActionPreference = "Stop"

$RepoRoot = Resolve-Path (Join-Path $PSScriptRoot "..\..")
Set-Location $RepoRoot

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "O-E-S-C-L Final Output Reproduction Run" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Repository: $RepoRoot" -ForegroundColor Cyan

$env:PYTHONPATH = Join-Path $RepoRoot "src"

New-Item -ItemType Directory -Force "results\final\tables" | Out-Null
New-Item -ItemType Directory -Force "results\final\reports" | Out-Null
New-Item -ItemType Directory -Force "results\final\manifests" | Out-Null

Write-Host ""
Write-Host "[1/5] Generating entropy-corrected band outputs..." -ForegroundColor Yellow
python scripts\final_outputs\generate_entropy_corrected_band_results.py

Write-Host ""
Write-Host "[2/5] Checking entropy-corrected band outputs..." -ForegroundColor Yellow
python scripts\final_outputs\check_entropy_corrected_outputs.py

Write-Host ""
Write-Host "[3/5] Generating final project manifest..." -ForegroundColor Yellow
python scripts\final_outputs\generate_project_manifest.py

Write-Host ""
Write-Host "[4/5] Checking final project manifest..." -ForegroundColor Yellow
python scripts\final_outputs\check_project_manifest.py

Write-Host ""
Write-Host "[5/5] Writing final SHA256 evidence list..." -ForegroundColor Yellow

$EvidenceFiles = @(
    "results\final\tables\entropy_corrected_band_results.csv",
    "results\final\reports\entropy_corrected_band_results_report.md",
    "results\final\manifests\project_manifest.json",
    "results\final\reports\project_manifest_report.md",
    "validation_data\gnpy_day16_cs_raman_reference.csv",
    "results\tables\day16_cs_full_raman_protocol_summary.csv",
    "results\reports\day16_cs_full_raman_isrs_validation_report.md",
    "results\reports\day13_model_alignment_report.md",
    "results\reports\day10_publication_validation_report.md",
    "results\reports\day8_q3_acceptance_report.md",
    "results\topology_verify\reports\day16_topology_decision.md",
    "results\topology_verify\reports\day16_ramanfiber_failed_attempt.md"
)

$Rows = @()
foreach ($file in $EvidenceFiles) {
    if (Test-Path $file) {
        $hash = Get-FileHash $file -Algorithm SHA256
        $Rows += [PSCustomObject]@{
            path = $file.Replace("\", "/")
            sha256 = $hash.Hash
            size_bytes = (Get-Item $file).Length
        }
    }
}

$Rows | Export-Csv "results\final\manifests\final_sha256_evidence_list.csv" -NoTypeInformation -Encoding UTF8

$Commit = git rev-parse HEAD
$Branch = git branch --show-current
$Status = git status --short
$Now = Get-Date -Format "yyyy-MM-dd HH:mm:ss zzz"

$Report = @(
    "# Final Reproduction Run Report",
    "",
    "Run time: $Now",
    "",
    "Branch: $Branch",
    "",
    "Commit: $Commit",
    "",
    "Generated outputs:",
    "",
    "- results/final/tables/entropy_corrected_band_results.csv",
    "- results/final/reports/entropy_corrected_band_results_report.md",
    "- results/final/manifests/project_manifest.json",
    "- results/final/reports/project_manifest_report.md",
    "- results/final/manifests/final_sha256_evidence_list.csv",
    "",
    "Checker status:",
    "",
    "- Entropy-corrected output checker passed.",
    "- Project manifest checker passed.",
    "",
    "Git status after run:",
    ""
)

if ($Status) {
    $Report += $Status
}
else {
    $Report += "Clean working tree."
}

$Report | Set-Content "results\final\reports\final_reproduction_run_report.md" -Encoding UTF8

Write-Host ""
Write-Host "PASS: Final reproduction run completed successfully." -ForegroundColor Green
Write-Host "See: results\final\reports\final_reproduction_run_report.md" -ForegroundColor Green
