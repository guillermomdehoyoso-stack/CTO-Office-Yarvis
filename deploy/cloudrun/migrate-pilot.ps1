[CmdletBinding(SupportsShouldProcess)]
param(
    [Parameter(Mandatory = $true)][string]$ProjectId,
    [Parameter(Mandatory = $true)][string]$Region,
    [Parameter(Mandatory = $true)][string]$JobName,
    [Parameter(Mandatory = $true)][string]$Image,
    [Parameter(Mandatory = $true)][string]$CloudSqlConnectionName,
    [Parameter(Mandatory = $true)][string]$RuntimeServiceAccount,
    [Parameter(Mandatory = $true)][string]$OidcIssuer,
    [Parameter(Mandatory = $true)][string]$OidcClientId,
    [Parameter(Mandatory = $true)][string]$OidcRedirectUri,
    [Parameter(Mandatory = $true)][string]$CorsOrigin
)

$ErrorActionPreference = 'Stop'
if ($PSCmdlet.ShouldProcess("Cloud Run job $JobName", 'run controlled Alembic migration')) {
    $environment = "YARVIS_ENVIRONMENT=production,YARVIS_AUTH_MODE=oidc,YARVIS_OIDC_ISSUER=$OidcIssuer,YARVIS_OIDC_CLIENT_ID=$OidcClientId,YARVIS_OIDC_REDIRECT_URI=$OidcRedirectUri,YARVIS_CORS_ORIGINS=$CorsOrigin,YARVIS_CSRF_ALLOWED_ORIGINS=$CorsOrigin,YARVIS_SESSION_COOKIE_NAME=__Host-yarvis_session,YARVIS_API_DOCS_ENABLED=false"
    gcloud run jobs create $JobName --project $ProjectId --region $Region --image $Image --service-account $RuntimeServiceAccount --add-cloudsql-instances $CloudSqlConnectionName --set-secrets 'YARVIS_DATABASE_URL=YARVIS_DATABASE_URL:latest,YARVIS_OIDC_CLIENT_SECRET=YARVIS_OIDC_CLIENT_SECRET:latest,YARVIS_OIDC_ATTEMPT_ENCRYPTION_KEY=YARVIS_OIDC_ATTEMPT_ENCRYPTION_KEY:latest' --set-env-vars $environment --command alembic --args upgrade,head --max-retries 0 --tasks 1 --parallelism 1
    gcloud run jobs execute $JobName --project $ProjectId --region $Region --wait
}
