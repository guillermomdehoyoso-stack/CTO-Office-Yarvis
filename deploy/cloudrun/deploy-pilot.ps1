[CmdletBinding(SupportsShouldProcess)]
param(
    [Parameter(Mandatory = $true)][ValidatePattern('^sha256:[a-f0-9]{64}$')][string]$ImageDigest,
    [Parameter(Mandatory = $true)][string]$CloudSqlConnectionName,
    [Parameter(Mandatory = $true)][string]$OidcIssuer,
    [Parameter(Mandatory = $true)][string]$OidcClientId,
    [Parameter(Mandatory = $true)][string]$OidcRedirectUri,
    [Parameter(Mandatory = $true)][string]$CorsOrigin
)

$ErrorActionPreference = 'Stop'
$ProjectId = 'yarvis-pilot'
$Region = 'northamerica-south1'
$ArtifactRepository = 'yarvis'
$ServiceName = 'yarvis-pilot'
$RuntimeServiceAccount = 'yarvis-pilot-runtime@yarvis-pilot.iam.gserviceaccount.com'
$image = "$Region-docker.pkg.dev/$ProjectId/$ArtifactRepository/yarvis-api@$ImageDigest"
$requiredSecrets = @(
    'YARVIS_DATABASE_URL',
    'YARVIS_OIDC_CLIENT_SECRET',
    'YARVIS_OIDC_ATTEMPT_ENCRYPTION_KEY'
)
$secretBindings = ($requiredSecrets | ForEach-Object { "$_=$_`:latest" }) -join ','
$environment = @(
    'YARVIS_ENVIRONMENT=production',
    'YARVIS_AUTH_MODE=oidc',
    'YARVIS_API_DOCS_ENABLED=false',
    'YARVIS_API_PORT=8080',
    'YARVIS_WEB_STATIC_ROOT=/app/web',
    'YARVIS_WORKSPACE_REPOSITORY_ROOT=/workspace-repository',
    'YARVIS_DOCUMENT_STORAGE_ROOT=/var/yarvis-documents',
    "YARVIS_OIDC_ISSUER=$OidcIssuer",
    "YARVIS_OIDC_CLIENT_ID=$OidcClientId",
    "YARVIS_OIDC_REDIRECT_URI=$OidcRedirectUri",
    "YARVIS_OIDC_POST_LOGIN_REDIRECT_ALLOWLIST=/",
    "YARVIS_CORS_ORIGINS=$CorsOrigin",
    "YARVIS_CSRF_ALLOWED_ORIGINS=$CorsOrigin",
    'YARVIS_SESSION_COOKIE_NAME=__Host-yarvis_session',
    'YARVIS_SESSION_IDLE_SECONDS=1800',
    'YARVIS_SESSION_ABSOLUTE_SECONDS=28800',
    'YARVIS_SESSION_MAX_ACTIVE=3',
    'YARVIS_BOOTSTRAP_ENABLED=false',
    'YARVIS_BOOTSTRAP_WINDOW_SECONDS=86400',
    'YARVIS_AUTH_DEPLOYMENT_REPLICAS=1',
    'YARVIS_AUTH_RATE_LIMIT_BACKEND=memory',
    'YARVIS_AUTH_CLEANUP_SESSION_RETENTION_DAYS=7'
) -join ','

Write-Output "Prepared image reference: $image"
Write-Output "Prepared migration command: gcloud run jobs execute $ServiceName-migrate --region $Region --project $ProjectId --wait"
if ($PSCmdlet.ShouldProcess("Cloud Run service $ServiceName", 'deploy restricted pilot')) {
    gcloud run deploy $ServiceName --project $ProjectId --region $Region --image $image --service-account $RuntimeServiceAccount --add-cloudsql-instances $CloudSqlConnectionName --set-secrets $secretBindings --set-env-vars $environment --max-instances 1 --min-instances 0 --port 8080 --allow-unauthenticated
}
