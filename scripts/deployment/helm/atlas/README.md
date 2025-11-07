# Atlas Helm Chart (OpenShift)

This chart deploys the Atlas application stack on OpenShift with the following components:

- Main App (Deployment + Service)
- Auth App (Deployment + Service)
- NGINX (Deployment + Service + Route)
- MinIO (Deployment + PVC + Service) — enabled by default

NGINX proxies requests to the main and auth services and exposes an OpenShift Route.

Additional persistent/config mounts provided:
- Logs PVC mounted at `APP_LOG_DIR` (default: `/app/backend/logs`).
- Feedback PVC mounted at `RUNTIME_FEEDBACK_DIR` (default: `/app/backend/runtime/feedback`).
- Config overrides ConfigMap mounted at `APP_CONFIG_OVERRIDES` (default path: `/app/config/overrides`).

## Install

Prerequisites:
- OpenShift cluster (or OKD)
- `helm` installed and logged into your cluster context

Example install into namespace `atlas`:

```bash
oc new-project atlas || oc project atlas
helm upgrade --install atlas ./scripts/deployment/helm/atlas \
  --set imagePullSecret.username=YOUR_USER \
  --set imagePullSecret.password=YOUR_TOKEN \
  --set images.mainApp.repository=ghcr.io/YOURORG/atlas-backend \
  --set images.authApp.repository=ghcr.io/YOURORG/atlas-auth
```

The Route will be created and host auto-generated unless `route.host` is set.

## Values overview

- `app.name`: Base name used in service/route naming.
- `images.*`: Repositories/tags for mainApp, authApp, nginx, minio.
- `imagePullSecret.*`: Create a docker-registry secret (or set `imagePullSecret.create=false` and populate `imagePullSecrets`).
- `replicaCount.*`: Replicas per component.
- `s3.useMinio`: If true, deploy MinIO and wire apps to it. Otherwise, set `s3.external.*`.
- `minio.persistence.*`: Enable PVC and size/class (defaults to 10Gi).
- `route.*`: Configure OpenShift Route (TLS edge by default).

## S3 wiring

The chart sets the following environment variables into Main and Auth apps:
- `S3_ENDPOINT`
- `S3_BUCKET`
- `S3_REGION`
- `S3_PATH_STYLE`
- `S3_ACCESS_KEY`
- `S3_SECRET_KEY`

If `s3.useMinio=true`, credentials come from Values (`minio.rootUser`, `minio.rootPassword`) via Secret `<release>-atlas-s3`.
If `s3.external.enabled=true`, provide an existing Secret via `s3.external.accessKeySecretName` with keys `accessKey` and `secretKey`.

## OpenShift specifics

- Uses OpenShift Route instead of Ingress.
- Pods run with `runAsNonRoot: true` and arbitrary UID (do not set `runAsUser`).
- The NGINX image defaults to an unprivileged build compatible with random UIDs.

## Uninstall

```bash
helm uninstall atlas
```

## Populate Config Overrides ConfigMap

The chart can mount configuration override files into the application using a ConfigMap. By default, if `configOverrides.enabled=true` and no `existingConfigMap` is specified, it creates a placeholder ConfigMap. To load real files from your repo’s `config/overrides` directory (or any path you supply), use the helper script.

### Script: `scripts/deployment/helm/atlas/scripts/populate-config-overrides.sh`

Purpose: packages files from a local directory into a ConfigMap named `<release>-atlas-config-overrides`.

Environment variables consumed by the backend:
- `APP_CONFIG_OVERRIDES` points to the mount path inside the container (from values: `configOverrides.mountPath`).

### Usage

1. Ensure you’ve installed or will install the chart with `configOverrides.enabled=true`:
  ```bash
  helm upgrade --install atlas ./scripts/deployment/helm/atlas \
    --set configOverrides.enabled=true
  ```

2. Populate the ConfigMap (before or after install):
  ```bash
  ./scripts/deployment/helm/atlas/scripts/populate-config-overrides.sh atlas atlas config/overrides
  ```
  Arguments:
  - `<release-name>`: Helm release (e.g. `atlas`)
  - `<namespace>`: Kubernetes namespace/project (e.g. `atlas`)
  - `[path-to-overrides]`: Optional; defaults to `config/overrides`

3. Confirm ConfigMap created:
  ```bash
  kubectl get configmap atlas-atlas-config-overrides -n atlas
  kubectl describe configmap atlas-atlas-config-overrides -n atlas
  ```

4. Pods will mount the ConfigMap at `/app/config/overrides` (or your overridden path) and the backend will read overrides via `APP_CONFIG_OVERRIDES`.

### Updating Overrides

Re-run the script any time files change:
```bash
./scripts/deployment/helm/atlas/scripts/populate-config-overrides.sh atlas atlas config/overrides
kubectl rollout restart deployment/atlas-atlas-main-app -n atlas
kubectl rollout restart deployment/atlas-atlas-auth-app -n atlas
```

### Notes

- Binary files are not recommended; all entries are stored as text.
- File names are flattened: subdirectories use `_` in the key (e.g. `subdir_settings.yml`).
- If you supply `configOverrides.existingConfigMap`, the script can still manage that name—pass the same release name and ensure the chart mounts it.

