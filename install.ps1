$ErrorActionPreference = "Stop"

$sourceDirectory = Split-Path -Parent $MyInvocation.MyCommand.Path
$petDirectory = Join-Path $env:USERPROFILE ".codex\pets\yain-ivan"

New-Item -ItemType Directory -Force -Path $petDirectory | Out-Null
Copy-Item -LiteralPath (Join-Path $sourceDirectory "pet.json") -Destination $petDirectory -Force
Copy-Item -LiteralPath (Join-Path $sourceDirectory "spritesheet.webp") -Destination $petDirectory -Force

Write-Host "야인이반 설치 완료: $petDirectory"
Write-Host "Codex의 펫 선택 화면을 새로고침하거나 앱을 재시작하세요."
