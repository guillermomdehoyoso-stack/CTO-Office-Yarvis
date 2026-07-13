param(
    [string]$ComposeFile,
    [string]$OutputDir,
    [string]$PostgresService = "postgres"
)

$ErrorActionPreference = "Stop"

$repoRoot = Split-Path -Parent $PSScriptRoot

if (-not $ComposeFile) {
    $ComposeFile = Join-Path $repoRoot "docker-compose.yml"
}

if (-not $OutputDir) {
    $OutputDir = Join-Path $repoRoot "backups"
}

if (-not (Test-Path -LiteralPath $OutputDir)) {
    New-Item -ItemType Directory -Path $OutputDir | Out-Null
}

if (-not (Test-Path -LiteralPath $ComposeFile)) {
    throw "docker-compose file not found: $ComposeFile"
}

$timestampUtc = (Get-Date).ToUniversalTime().ToString("yyyyMMddTHHmmssZ")
$fileName = "yarvis_backup_$timestampUtc.dump"
$outputPath = Join-Path $OutputDir $fileName
$containerDumpPath = "/tmp/$fileName"
$containerListPath = "/tmp/${fileName}.list"

Write-Host "Creating PostgreSQL backup at: $outputPath"

try {
    docker compose -f $ComposeFile exec -T $PostgresService sh -lc "pg_dump -U `"`$POSTGRES_USER`" -d `"`$POSTGRES_DB`" -Fc -f $containerDumpPath"
    if ($LASTEXITCODE -ne 0) {
        throw "pg_dump failed"
    }

    docker compose -f $ComposeFile cp "${PostgresService}:$containerDumpPath" $outputPath | Out-Null
    if ($LASTEXITCODE -ne 0) {
        throw "Failed to copy backup file from container"
    }

    if (-not (Test-Path -LiteralPath $outputPath)) {
        throw "Backup file was not created"
    }

    $fileInfo = Get-Item -LiteralPath $outputPath
    if ($fileInfo.Length -le 0) {
        throw "Backup file is empty: $outputPath"
    }

    docker compose -f $ComposeFile cp $outputPath "${PostgresService}:$containerDumpPath" | Out-Null
    if ($LASTEXITCODE -ne 0) {
        throw "Failed to copy backup file back to container for validation"
    }

    docker compose -f $ComposeFile exec -T $PostgresService sh -lc "pg_restore --list $containerDumpPath > $containerListPath"
    if ($LASTEXITCODE -ne 0) {
        throw "pg_restore --list validation failed"
    }

    $hash = Get-FileHash -LiteralPath $outputPath -Algorithm SHA256

    Write-Host "Backup completed successfully"
    Write-Host "File: $outputPath"
    Write-Host "Size: $($fileInfo.Length) bytes"
    Write-Host "SHA256: $($hash.Hash)"
}
finally {
    docker compose -f $ComposeFile exec -T $PostgresService sh -lc "rm -f $containerDumpPath $containerListPath" | Out-Null
}
