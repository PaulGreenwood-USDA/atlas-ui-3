#!/usr/bin/env bash
set -euo pipefail

# This helper generates a Helm template YAML for a ConfigMap from local config/overrides directory
# and writes it under templates/configmap-config-overrides-generated.yaml for inclusion in the chart.
#
# Usage:
#   ./scripts/deployment/helm/atlas/scripts/populate-config-overrides.sh <release-name> <namespace> [path-to-overrides]
#
# It will create/overwrite templates/configmap-config-overrides-generated.yaml with file entries.
# You can commit this file or keep it untracked depending on your workflow.

if [[ $# -lt 2 ]]; then
  echo "Usage: $0 <release-name> <namespace> [path-to-overrides]" >&2
  exit 1
fi

RELEASE="$1"
NAMESPACE="$2"
OVERRIDES_DIR="${3:-config/overrides}"
CHART_NAME="atlas"
CM_NAME="${RELEASE}-${CHART_NAME}-config-overrides"

if [[ ! -d "$OVERRIDES_DIR" ]]; then
  echo "Directory '$OVERRIDES_DIR' not found. Provide path to overrides or create it." >&2
  exit 1
fi

echo "Building ConfigMap $CM_NAME from $OVERRIDES_DIR"

OUT_FILE="scripts/deployment/helm/atlas/templates/configmap-config-overrides-generated.yaml"
mkdir -p "$(dirname "$OUT_FILE")"
cat > "$OUT_FILE" <<EOF
apiVersion: v1
kind: ConfigMap
metadata:
  name: $CM_NAME
  labels:
    app.kubernetes.io/instance: $RELEASE
    app.kubernetes.io/name: $CHART_NAME
    managed-by: populate-config-overrides.sh
    component: config-overrides
data:
EOF

# Add each file as key with its contents. Strip leading './'
while IFS= read -r -d '' file; do
  rel="${file#./}"
  rel="${rel#${OVERRIDES_DIR}/}"   # relative path inside overrides dir
  key=$(echo "$rel" | tr '/' '_' )
  echo "  Adding $file as key $key"
  printf "  %s: |\n" "$key" >> "$OUT_FILE"
  sed 's/^/    /' "$file" >> "$OUT_FILE"
  echo >> "$OUT_FILE"
done < <(find "$OVERRIDES_DIR" -type f -print0)

echo "Wrote ConfigMap template: $OUT_FILE"
echo "Next: helm upgrade --install $RELEASE ./scripts/deployment/helm/atlas"
echo "Mounted at /app/config/overrides when installed with configOverrides.enabled=true."
