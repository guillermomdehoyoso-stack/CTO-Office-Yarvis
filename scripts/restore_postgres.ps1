param(
    [Parameter(Mandatory = $true)]
    [string]$BackupFile,
    [string]$ComposeFile,
    [string]$PostgresService = "postgres",
    [string]$TargetDatabase = "yarvis_restore_test"
)

$ErrorActionPreference = "Stop"

$repoRoot = Split-Path -Parent $PSScriptRoot

if (-not $ComposeFile) {
    $ComposeFile = Join-Path $repoRoot "docker-compose.yml"
}

if ($TargetDatabase -notmatch '^[a-zA-Z0-9_]+$') {
    throw "TargetDatabase contains invalid characters. Use only letters, numbers, and underscore."
}

$blockedDatabases = @("yarvis", "postgres", "template0", "template1")
if ($blockedDatabases -contains $TargetDatabase) {
    throw "TargetDatabase '$TargetDatabase' is blocked. Use a temporary restore database such as 'yarvis_restore_test'."
}

if (-not (Test-Path -LiteralPath $ComposeFile)) {
    throw "docker-compose file not found: $ComposeFile"
}

if (-not (Test-Path -LiteralPath $BackupFile)) {
    throw "Backup file not found: $BackupFile"
}

Write-Host "Restoring backup into $TargetDatabase"
$timestampUtc = (Get-Date).ToUniversalTime().ToString("yyyyMMddTHHmmssZ")
$containerDumpPath = "/tmp/yarvis_restore_$timestampUtc.dump"
$containerListPath = "/tmp/yarvis_restore_$timestampUtc.list"

try {
    docker compose -f $ComposeFile cp $BackupFile "${PostgresService}:$containerDumpPath" | Out-Null
    if ($LASTEXITCODE -ne 0) {
        throw "Failed to copy backup into container"
    }

    docker compose -f $ComposeFile exec -T $PostgresService sh -lc "pg_restore --list $containerDumpPath > $containerListPath"
    if ($LASTEXITCODE -ne 0) {
        throw "pg_restore --list validation failed"
    }

    Write-Host "You are about to restore backup '$BackupFile' into database '$TargetDatabase'."
    $confirmation = Read-Host "Type RESTORE to continue"
    if ($confirmation -ne "RESTORE") {
        throw "Restore cancelled by user"
    }

    Write-Host "Preparing target database: $TargetDatabase"
    docker compose -f $ComposeFile exec -T $PostgresService sh -lc "psql -U `"`$POSTGRES_USER`" -d postgres -v ON_ERROR_STOP=1 -c 'DROP DATABASE IF EXISTS $TargetDatabase'" | Out-Null
    if ($LASTEXITCODE -ne 0) {
        throw "Failed to drop target database: $TargetDatabase"
    }

    docker compose -f $ComposeFile exec -T $PostgresService sh -lc "psql -U `"`$POSTGRES_USER`" -d postgres -v ON_ERROR_STOP=1 -c 'CREATE DATABASE $TargetDatabase'" | Out-Null
    if ($LASTEXITCODE -ne 0) {
        throw "Failed to create target database: $TargetDatabase"
    }

    docker compose -f $ComposeFile exec -T $PostgresService sh -lc "pg_restore -U `"`$POSTGRES_USER`" -d `"$TargetDatabase`" --no-owner --no-privileges $containerDumpPath" | Out-Null
    if ($LASTEXITCODE -ne 0) {
        throw "pg_restore failed for target database: $TargetDatabase"
    }

    docker compose -f $ComposeFile exec -T $PostgresService sh -lc "psql -U `"`$POSTGRES_USER`" -d `"$TargetDatabase`" -v ON_ERROR_STOP=1 -c 'SELECT 1'" | Out-Null
    if ($LASTEXITCODE -ne 0) {
        throw "Connection validation failed for target database: $TargetDatabase"
    }

    docker compose -f $ComposeFile exec -T $PostgresService sh -lc "psql -U `"`$POSTGRES_USER`" -d `"$TargetDatabase`" -v ON_ERROR_STOP=1 -c \"SELECT CASE WHEN EXISTS (SELECT 1 FROM information_schema.tables WHERE table_schema='public' AND table_name='alembic_version') OR EXISTS (SELECT 1 FROM information_schema.tables WHERE table_schema='public' AND table_name='cases') THEN 1 ELSE 0 END;\"" | Out-Null
    if ($LASTEXITCODE -ne 0) {
        throw "Post-restore table verification failed for target database: $TargetDatabase"
    }

    Write-Host "Restore completed successfully"
    Write-Host "Target database: $TargetDatabase"
}
finally {
    docker compose -f $ComposeFile exec -T $PostgresService sh -lc "rm -f $containerDumpPath $containerListPath" | Out-Null
}
