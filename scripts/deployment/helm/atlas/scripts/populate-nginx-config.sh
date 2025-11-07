#!/usr/bin/env bash
set -euo pipefail

# Generate a Helm template ConfigMap for NGINX config instead of applying directly to the cluster.
# Writes templates/configmap-nginx-generated.yaml containing file contents under the chosen key.
#
# Usage:
#   ./scripts/deployment/helm/atlas/scripts/populate-nginx-config.sh <release> <namespace> [config-file]
#
# Defaults:
#   config-file: scripts/deployment/helm/atlas/nginx/default.conf
#   key: default.conf (override via env NGINX_CONFIG_KEY)
#   configmap name: <release>-atlas-nginx-conf (override via env NGINX_CONFIGMAP_NAME)
#
# After generation, install chart with: --set nginx.configMapName=<name> --set nginx.configKey=<key>

if [[ $# -lt 2 ]]; then
  echo "Usage: $0 <release> <namespace> [config-file]" >&2
  exit 1
fi

RELEASE="$1"
NAMESPACE="$2"  # namespace retained for reference (not embedded)
FILE_PATH="${3:-scripts/deployment/helm/atlas/nginx/default.conf}"
CHART_NAME="atlas"
CONFIG_KEY="${NGINX_CONFIG_KEY:-default.conf}"
CONFIGMAP_NAME="${NGINX_CONFIGMAP_NAME:-${RELEASE}-${CHART_NAME}-nginx-conf}"

if [[ ! -f "$FILE_PATH" ]]; then
  echo "Config file not found: $FILE_PATH" >&2
  exit 1
fi

# Build ConfigMap YAML
OUT_FILE="scripts/deployment/helm/atlas/templates/configmap-nginx-generated.yaml"
mkdir -p "$(dirname "$OUT_FILE")"
cat > "$OUT_FILE" <<EOF
{{- if .Values.nginx.configMapName }}
apiVersion: v1
kind: ConfigMap
metadata:
  name: $CONFIGMAP_NAME
  labels:
    app.kubernetes.io/instance: $RELEASE
    app.kubernetes.io/name: $CHART_NAME
    component: nginx
    managed-by: populate-nginx-config.sh
data:
  $CONFIG_KEY: |
EOF
sed 's/^/    /' "$FILE_PATH" >> "$OUT_FILE"
cat >> "$OUT_FILE" <<EOF
{{- end }}
EOF

echo "Wrote NGINX ConfigMap template: $OUT_FILE"
echo "Install/upgrade with: --set nginx.configMapName=$CONFIGMAP_NAME --set nginx.configKey=$CONFIG_KEY"
