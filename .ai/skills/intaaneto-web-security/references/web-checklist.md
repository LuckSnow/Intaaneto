# Web security checklist

## Authentication and sessions

- Use tested password validation and hashing; never log passwords or full
  registration payloads.
- Verify email/token expiry, replay behavior, resend throttling, and enumeration
  resistance.
- Verify JWT refresh rotation and blacklist configuration end to end.
- Keep token handling consistent; document the accepted XSS tradeoff if tokens
  remain in `localStorage`.
- Rate-limit login, registration, resend, refresh, upload, AI, and assessment.

## API and data

- Use explicit serializer fields and action-specific serializers.
- Validate ownership and parent relationships for every foreign key.
- Paginate and bound list endpoints, history, comments, and search.
- Prevent mass assignment of role, owner, status, score, publication, progress,
  provider IDs, and internal metadata.
- Return stable error codes without secrets, SQL, paths, prompts, or provider
  credentials.
- Protect Swagger/admin/debug endpoints appropriately outside development.

## Upload and object storage

- Use private buckets by default and short-lived signed URLs where required.
- Generate object keys server-side and scope them by environment/resource ID.
- Configure CORS narrowly, block public listing, and restrict credential policy.
- Validate size and content before or during streaming; clean incomplete uploads.
- Verify webhook/callback signatures and prevent server-side request forgery when
  fetching external URLs.

## Frontend

- Do not put secrets in `VITE_*`; they are embedded into the browser bundle.
- Avoid raw HTML injection; sanitize rich content under an explicit policy.
- Treat route guards as UX only and enforce all access on the backend.
- Avoid rendering raw provider/backend errors.
- Review dependencies and lockfile changes; do not run automated major-version
  audit fixes without tests.

## Deployment and secrets

- Disable debug, rotate default secrets, restrict hosts/CORS/CSRF, and use HTTPS.
- Do not hard-code database passwords in production configuration.
- Run migrations as an explicit, observable deployment step.
- Use health checks and start dependencies in a retry-safe way.
- Separate dev/test/prod databases, buckets, keys, callbacks, and logs.
- Pin compatible dependencies, scan them in CI, and add secret scanning.
- Back up database/object metadata and test restore and deletion procedures.

## Verification commands

Choose commands supported by the repository and environment:

```text
python manage.py check --deploy
python manage.py makemigrations --check --dry-run
pytest
flake8
npm run lint
npm run build
npm audit
```

Command success is evidence, not proof. Pair it with role/object negative tests
and direct inspection of querysets, serializers, custom actions, and settings.

