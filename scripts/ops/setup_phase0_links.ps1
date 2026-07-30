# Create hardlinks so local assets/ reuse checkpoints without duplicating files.
# Runtime code reads assets/ and third_party/ only — never GitHubSourceCode/.
# Run from repository root in PowerShell.

$root = Split-Path -Parent (Split-Path -Parent $PSScriptRoot)

function Ensure-HardLink($link, $target) {
    if (-not (Test-Path $target)) {
        Write-Host "SKIP missing target: $target"
        return
    }
    $dir = Split-Path -Parent $link
    if (-not (Test-Path $dir)) {
        New-Item -ItemType Directory -Force -Path $dir | Out-Null
    }
    if (Test-Path $link) {
        Write-Host "OK exists: $link"
        return
    }
    cmd /c mklink /H "$link" "$target" | Out-Null
    Write-Host "LINKED $link -> $target"
}

# Prefer survey-tree checkpoints if present locally (setup aid only).
Ensure-HardLink `
    "$root\assets\nesymres\weights\100M.ckpt" `
    "$root\GitHubSourceCode\NSRS\weights\100M.ckpt"

Ensure-HardLink `
    "$root\assets\nesymres\weights\10M.ckpt" `
    "$root\GitHubSourceCode\NSRS\weights\10M.ckpt"

Ensure-HardLink `
    "$root\assets\nesymres\weights\model.pt" `
    "$root\GitHubSourceCode\TPSR\symbolicregression\weights\model1.pt"

Ensure-HardLink `
    "$root\assets\nesymres\weights\model1.pt" `
    "$root\GitHubSourceCode\TPSR\symbolicregression\weights\model1.pt"
