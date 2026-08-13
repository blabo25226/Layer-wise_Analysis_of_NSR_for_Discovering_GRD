# Sequential GPU_RUN2 runner for the local Windows RTX 2070 PC.
# Usage:
#   powershell -File scripts/ops/run_gpu_run2.ps1
#   powershell -File scripts/ops/run_gpu_run2.ps1 -Smoke
#   powershell -File scripts/ops/run_gpu_run2.ps1 -FromPhase 3
#   powershell -File scripts/ops/run_gpu_run2.ps1 -DryRun
param(
    [string]$RunId = $(if ($env:LANSR_RUN_ID) { $env:LANSR_RUN_ID } else { "gpu_run2_local" }),
    [int]$FromPhase = 0,
    [switch]$Smoke,
    [switch]$DryRun,
    [switch]$AllowCpu,
    [switch]$SkipArchive
)

$ErrorActionPreference = "Stop"
$RepoRoot = Resolve-Path (Join-Path $PSScriptRoot "..\..")
Set-Location $RepoRoot

$env:LANSR_RUN_ID = $RunId
$env:LANSR_DECODE_TIMEOUT_SEC = "30"
$RunDir = Join-Path $RepoRoot "results\runs\$RunId"
$env:LANSR_RUN_DIR = $RunDir
New-Item -ItemType Directory -Force -Path $RunDir | Out-Null

function Invoke-Phase {
    param(
        [int]$Phase,
        [string]$Script,
        [string[]]$ExtraArgs = @()
    )
    if ($Phase -lt $FromPhase) {
        Write-Host "Skipping Phase $Phase (FromPhase=$FromPhase)"
        return
    }
    Write-Host "=== GPU_RUN2 Phase $Phase ==="
    $argsList = @($Script) + $ExtraArgs
    python @argsList
    if ($LASTEXITCODE -ne 0) {
        throw "Phase $Phase failed with exit code $LASTEXITCODE"
    }
}

$common = @("--run-id", $RunId)
if ($Smoke) { $common += "--smoke" }
if ($DryRun) { $common += "--dry-run" }

$phase0 = @("scripts/phases/gpu_run2_phase0_preflight.py", "--run-id", $RunId)
if ($AllowCpu) { $phase0 += "--allow-cpu" }
Invoke-Phase -Phase 0 -Script $phase0[0] -ExtraArgs $phase0[1..($phase0.Length-1)]

Invoke-Phase -Phase 1 -Script "scripts/phases/gpu_run2_phase1_data.py" -ExtraArgs $common
Invoke-Phase -Phase 2 -Script "scripts/phases/gpu_run2_phase2_baseline.py" -ExtraArgs ($common + @("--split", "validation"))
Invoke-Phase -Phase 2 -Script "scripts/phases/gpu_run2_phase2_baseline.py" -ExtraArgs ($common + @("--split", "test"))
Invoke-Phase -Phase 3 -Script "scripts/phases/gpu_run2_phase3_interpret.py" -ExtraArgs $common
Invoke-Phase -Phase 4 -Script "scripts/phases/gpu_run2_phase4_contribution.py" -ExtraArgs $common
Invoke-Phase -Phase 5 -Script "scripts/phases/gpu_run2_phase5_selective_ft.py" -ExtraArgs ($common + @("--view", "main", "--split", "validation"))
Invoke-Phase -Phase 5 -Script "scripts/phases/gpu_run2_phase5_selective_ft.py" -ExtraArgs ($common + @("--view", "structure_holdout", "--split", "validation"))
Invoke-Phase -Phase 5 -Script "scripts/phases/gpu_run2_phase5_selective_ft.py" -ExtraArgs ($common + @("--view", "main", "--split", "test"))
Invoke-Phase -Phase 5 -Script "scripts/phases/gpu_run2_phase5_selective_ft.py" -ExtraArgs ($common + @("--view", "structure_holdout", "--split", "test"))

$finalize = @("scripts/ops/finalize_gpu_run2.py", "--run-id", $RunId)
if ($SkipArchive) { $finalize += "--skip-archive" }
Write-Host "=== GPU_RUN2 finalize ==="
python @finalize
if ($LASTEXITCODE -ne 0) {
    throw "finalize failed with exit code $LASTEXITCODE"
}
Write-Host "GPU_RUN2 finished. Run dir: $RunDir"
