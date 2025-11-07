# Atlas Helm Chart (OpenShift)

This chart deploys the Atlas application stack on OpenShift with the following components:

- Main App (Deployment + Service)
- Auth App (Deployment + Service)
- NGINX (Deployment + Service + Route)
- MinIO (Deployment + PVC + Service) — enabled by default

NGINX proxies requests to the main and auth services and exposes an OpenShift Route.

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
