param(
    [string]$Scenario = "All",
    [int]$StartSeed = 21,
    [int]$EndSeed = 50,
    [int]$MaxJobs = 0,
    [switch]$DryRun,
    [switch]$Force
)

$ErrorActionPreference = "Stop"

$RepoRoot = Resolve-Path (Join-Path $PSScriptRoot "..\..")
Set-Location $RepoRoot

$JobList = "results\final\tables\confirmation_job_list.csv"

if (-not (Test-Path $JobList)) {
    throw "Missing job list: $JobList. Run generate_confirmation_job_list.py first."
}

New-Item -ItemType Directory -Force "results\final\raw_confirmation" | Out-Null
New-Item -ItemType Directory -Force "results\final\logs" | Out-Null
New-Item -ItemType Directory -Force "results\final\reports" | Out-Null

$jobs = Import-Csv $JobList

$jobs = $jobs | Where-Object {
    ([int]$_.seed -ge $StartSeed) -and
    ([int]$_.seed -le $EndSeed)
}

if ($Scenario -ne "All") {
    $jobs = $jobs | Where-Object { $_.scenario -eq $Scenario }
}

if ($MaxJobs -gt 0) {
    $jobs = $jobs | Select-Object -First $MaxJobs
}

$total = ($jobs | Measure-Object).Count
$done = 0
$skipped = 0
$failed = 0

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "O-E-S-C-L Confirmation Batch Runner" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Scenario filter: $Scenario"
Write-Host "Seed range: $StartSeed to $EndSeed"
Write-Host "MaxJobs: $MaxJobs"
Write-Host "DryRun: $DryRun"
Write-Host "Force: $Force"
Write-Host "Jobs selected: $total"
Write-Host ""

$runStart = Get-Date

foreach ($job in $jobs) {
    $output = $job.output_csv
    $log = $job.log_path

    if ((Test-Path $output) -and (-not $Force) -and (-not $DryRun)) {
        Write-Host "SKIP existing: $($job.job_id)" -ForegroundColor DarkYellow
        $skipped += 1
        continue
    }

    Write-Host "RUN: $($job.job_id) | scenario=$($job.scenario) seed=$($job.seed)" -ForegroundColor Yellow

    $argsList = @(
        "scripts\final_outputs\run_single_confirmation_job.py",
        "--scenario", $job.scenario,
        "--seed", $job.seed,
        "--symbols", $job.symbols,
        "--nu", $job.nu,
        "--spans", $job.spans,
        "--launch-power-dbm", $job.launch_power_dbm,
        "--output", $output,
        "--log", $log
    )

    if ($DryRun) {
        $argsList += "--dry-run"
    }

    try {
        & python @argsList
        if ($LASTEXITCODE -ne 0) {
            throw "Python exited with code $LASTEXITCODE"
        }
        $done += 1
    }
    catch {
        $failed += 1
        Write-Host "FAILED: $($job.job_id)" -ForegroundColor Red
        Write-Host $_.Exception.Message -ForegroundColor Red
        break
    }
}

$runEnd = Get-Date
$elapsed = $runEnd - $runStart

$summary = @(
    "# Confirmation Batch Run Summary",
    "",
    "Start: $runStart",
    "End: $runEnd",
    "Elapsed: $elapsed",
    "",
    "Scenario filter: $Scenario",
    "Seed range: $StartSeed to $EndSeed",
    "MaxJobs: $MaxJobs",
    "DryRun: $DryRun",
    "Force: $Force",
    "",
    "Jobs selected: $total",
    "Jobs executed: $done",
    "Jobs skipped: $skipped",
    "Jobs failed: $failed"
)

$summary | Set-Content "results\final\reports\confirmation_batch_run_summary.md" -Encoding UTF8

if ($failed -gt 0) {
    throw "Batch stopped with $failed failed job(s)."
}

Write-Host ""
Write-Host "PASS: Batch completed." -ForegroundColor Green
Write-Host "Executed: $done | Skipped: $skipped | Failed: $failed" -ForegroundColor Green