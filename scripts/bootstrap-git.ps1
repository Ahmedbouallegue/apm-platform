# Bootstrap Sprint 0 — Git + premier commit + dépôt GitHub (à lancer en local)
# Usage (PowerShell, depuis la racine du projet) :
#   .\scripts\bootstrap-git.ps1 [-GitHubRepo "OWNER/apm-platform"]

param(
    [string]$GitHubRepo = ""
)

$ErrorActionPreference = "Stop"
Set-Location (Split-Path -Parent $PSScriptRoot)

if (-not (Test-Path .git)) {
    git init
    git branch -M main
}

git add -A
git status

$pending = git status --porcelain
if ($pending) {
    git commit -m "chore: bootstrap Sprint 0 — APM platform foundation"
} else {
    Write-Host "Nothing to commit."
}

if ($GitHubRepo) {
    gh repo create $GitHubRepo --private --source=. --remote=origin --push
    Write-Host "GitHub repository ready: https://github.com/$GitHubRepo"
} else {
    Write-Host @"

Prochaines étapes GitHub :
  gh auth login
  gh repo create apm-platform --private --source=. --remote=origin --push

Ou crée le repo sur github.com puis :
  git remote add origin https://github.com/<USER>/apm-platform.git
  git push -u origin main
"@
}
