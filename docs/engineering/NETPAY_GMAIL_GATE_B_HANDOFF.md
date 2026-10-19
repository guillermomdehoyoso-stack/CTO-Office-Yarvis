# Netpay Gmail Gate B operator handoff

Status: **Gate B PASS — 2026-10-10**. Gate C is ready for its single manual restricted pilot.

Workspace administration status: `UNVERIFIED`. The pilot operator cannot enter Google Admin
Console because Google requires an administrator account. This fact does not establish that the
OAuth client is blocked; the effective Workspace policy remains `UNKNOWN` until a bounded
consent attempt succeeds or Google returns an administrative denial.

## Existing-project reuse check

The existing project is accepted as the reuse candidate for Gate B based on the non-secret
operator record and local client-file validation:

- display name: `Yarvis Pilot`;
- project ID: `yarvis-pilot`;
- project number: `1030218466633`;
- organization: `netpay.com.mx`;
- Gmail API: enabled;
- OAuth audience: Internal;
- separate Web application client: `Yarvis Netpay Intake`; and
- exact redirect URI: `http://127.0.0.1:8000/netpay/gmail/oauth/callback`.

Exactly one supplied JSON candidate was found. It parsed as a Google Web application client,
matched the project ID/project-number prefix and exact callback, and contained the required
client fields and standard Google endpoints. Its secret values were neither printed nor copied
into the repository. No second project is proposed.

Reuse remains conditional on the Workspace and scope checks below. Project Owner in Google
Cloud is not evidence of Google Workspace administration. Verify what is available offline and
record the effective policy through the bounded consent check described below:

1. Yarvis authority owns/administers the project.
2. Organization policy permits Gmail API and OAuth consent configuration.
3. Gmail API is enabled or may be enabled.
4. The audience can be restricted to the authorized pilot account.
5. A distinct **Web application** OAuth client can be created for the pilot.
6. That client is separate from Yarvis OIDC login clients and secrets.
7. Only the exact Gmail readonly scope can be configured.

If Google returns an administrative denial and an authorized Workspace administrator cannot
approve the bounded access, Gate B fails closed. Lack of Google Admin Console access by the
pilot operator alone is not recorded as an OAuth denial. A fallback project would require a
separate recorded decision; it is not created by this handoff.

## Authority for the bounded consent check

IG-008 §4.B.4 requires recording whether Workspace Admin trust is required; it does not require
an administrator-console login as a precondition to starting OAuth. IG-008 §4.B.10 then requires
connecting and validating the mailbox and exact label. IG-008 §9 opens Google intervention after
Gate A evidence is accepted, while keeping content ingestion closed until Gate B and manifest
acceptance. Amendment 020 §12 Gate B requires the verified mailbox profile and label ID, which
are obtainable only through the consent/callback path.

Therefore the ratified authority permits one normal consent attempt as a test of the effective
policy after the exact scope, local mailbox binding and label name are ready. The attempt:

- requests only `https://www.googleapis.com/auth/gmail.readonly`;
- is bound to the pilot Principal, Organization and expected mailbox;
- calls only Gmail profile and label-list endpoints after token exchange;
- does not list, fetch, persist or analyze messages; and
- stops on user denial, administrative denial, mailbox mismatch, label absence or any unexpected
  scope/error.

No separate amendment is required for this check. Metadata manifest discovery is a subsequent,
explicit action and must not be selected during the consent-policy test.

## Exact Google Console steps

1. Select the existing Yarvis project. Record only project display name, project ID, project
   number, owning organization and project administrator.
2. In **APIs & Services**, confirm/enable **Gmail API**. Do not enable Pub/Sub.
3. In **Google Auth Platform / OAuth consent screen**, record audience (`Internal` when the
   mailbox is in the same Workspace organization; otherwise `External` in testing), publishing
   status and whether the pilot mailbox can be the sole test user.
4. Configure exactly `https://www.googleapis.com/auth/gmail.readonly` and no broader scope.
5. Confirm the distinct client:
   - type: `Web application`;
   - name: `Yarvis Netpay Intake`;
   - redirect URI: `http://127.0.0.1:8000/netpay/gmail/oauth/callback`;
   - authorized JavaScript origins: none.
6. Put client ID and client secret directly into protected local files. Never put them in chat,
   Git, screenshots, evidence or ordinary logs.
7. In Gmail, create/confirm label `Yarvis/Netpay-Intake` and apply it only to pilot messages.
8. Workspace administration is currently `UNVERIFIED`. If an administrator becomes available,
   that account may inspect **Security > Access and data control > API controls > Manage App
   Access**. Until then, do not infer blocked/allowed status from the operator's inability to
   enter Admin Console.
9. After confirming the exact scope, creating the label and local binding, one consent attempt
   may determine the effective policy. Do not select manifest discovery or synchronization.

The protected local mailbox binding is now present and passes preflight. The local runtime uses
one `netpay_inbox_operator` Membership in `Netpay Gmail Pilot`; its only effective permissions are
`netpay.inbox.read` and `netpay.inbox.manage`. Refresh the UI after the corrected web container
starts. Scope and label confirmation remain required before selecting Connect Gmail.

## Exact local values after Gate B acceptance

Use `%LOCALAPPDATA%\Yarvis\gmail-pilot` outside the repository with current-user-only access.
Store `client-id.txt`, `client-secret.txt`, `token-key.txt` (URL-safe base64 of exactly 32 random
bytes) and an encrypted `tokens\` directory. Then configure:

```text
YARVIS_GMAIL_INTAKE_ENABLED=true
YARVIS_GMAIL_PROVIDER=google
YARVIS_GMAIL_GOOGLE_PROJECT_ID=<verified project ID>
YARVIS_GMAIL_OAUTH_REDIRECT_URI=http://127.0.0.1:8000/netpay/gmail/oauth/callback
YARVIS_GMAIL_OAUTH_SCOPES=https://www.googleapis.com/auth/gmail.readonly
YARVIS_GMAIL_OAUTH_CLIENT_ID_FILE=%LOCALAPPDATA%\Yarvis\gmail-pilot\client-id.txt
YARVIS_GMAIL_OAUTH_CLIENT_SECRET_FILE=%LOCALAPPDATA%\Yarvis\gmail-pilot\client-secret.txt
YARVIS_GMAIL_TOKEN_KEY_FILE=%LOCALAPPDATA%\Yarvis\gmail-pilot\token-key.txt
YARVIS_GMAIL_TOKEN_STORE_ROOT=%LOCALAPPDATA%\Yarvis\gmail-pilot\tokens
YARVIS_GMAIL_MAILBOX_BINDING=file-aesgcm://netpay-gmail/binding
YARVIS_GMAIL_LABEL_NAME=Yarvis/Netpay-Intake
YARVIS_GMAIL_BACKFILL_DAYS=30
YARVIS_SCHEDULER_ENABLED=false
YARVIS_WORKER_ENABLED=false
```

The local runtime is available at `http://127.0.0.1:5173/netpay-inbox/gmail`. **Connect Gmail must
not be selected until the exact scope, local mailbox binding and label are confirmed.** The
provider authorization URL is generated at that time with one-time state and PKCE, so it must
not be precomputed or recorded. A successful callback validates only the mailbox profile and
exact label. Metadata-only discovery is a separate operator action. Message content stays closed
until acceptance of exactly 10 HMAC manifest entries. Gate C remains a later one-run decision.
