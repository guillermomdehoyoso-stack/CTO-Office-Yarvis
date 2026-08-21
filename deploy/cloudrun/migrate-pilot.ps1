[CmdletBinding(SupportsShouldProcess)]
param(
    [Parameter(Mandatory = $true)][ValidatePattern('^sha256:[a-f0-9]{64}$')][string]$ImageDigest,
    [Parameter(Mandatory = $true)][string]$CloudSqlConnectionName,
    [Parameter(Mandatory = $true)][string]$MigrationServiceAccount
)

$ErrorActionPreference = 'Stop'
$ProjectId = 'yarvis-pilot'
$Region = 'northamerica-south1'
$ArtifactRepository = 'yarvis'
$JobName = 'yarvis-pilot-migrate'
$RuntimeServiceAccount = 'yarvis-pilot-runtime@yarvis-pilot.iam.gserviceaccount.com'
if ($MigrationServiceAccount -eq $RuntimeServiceAccount) {
    throw 'MigrationServiceAccount must be distinct from the runtime service account.'
}
$image = "$Region-docker.pkg.dev/$ProjectId/$ArtifactRepository/yarvis-api@$ImageDigest"
if ($PSCmdlet.ShouldProcess("Cloud Run job $JobName", 'run controlled Alembic migration')) {
    gcloud run jobs create $JobName --project $ProjectId --region $Region --image $image --service-account $MigrationServiceAccount --add-cloudsql-instances $CloudSqlConnectionName --set-secrets 'YARVIS_MIGRATOR_DATABASE_URL=YARVIS_MIGRATOR_DATABASE_URL:latest' --command alembic --args upgrade,head --max-retries 0 --tasks 1 --parallelism 1
    gcloud run jobs execute $JobName --project $ProjectId --region $Region --wait
}
