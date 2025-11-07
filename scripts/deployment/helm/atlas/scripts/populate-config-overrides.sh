#!/usr/bin/env bash
set -euo pipefail

# This helper populates the chart's ConfigMap data from local config/overrides directory
# Usage:
#   ./scripts/deployment/helm/atlas/scripts/populate-config-overrides.sh <release-name> <namespace>
# It will create/replace a ConfigMap named <release>-atlas-config-overrides with file entries.
# Requires: kubectl/oc, yq (optional for merging), bash.

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

tmpfile=$(mktemp)
cat > "$tmpfile" <<EOF
apiVersion: v1
kind: ConfigMap
metadata:
  name: $CM_NAME
  namespace: $NAMESPACE
  labels:
    app.kubernetes.io/instance: $RELEASE
    app.kubernetes.io/name: $CHART_NAME
    managed-by: populate-script
    component: config-overrides
data:
EOF

# Add each file as key with its contents. Strip leading './'
while IFS= read -r -d '' file; do
  rel="${file#./}"
  rel="${rel#${OVERRIDES_DIR}/}"   # relative path inside overrides dir
  key=$(echo "$rel" | tr '/' '_' )
  echo "  Adding $file as key $key"
  printf "  %s: |\n" "$key" >> "$tmpfile"
  sed 's/^/    /' "$file" >> "$tmpfile"
  echo >> "$tmpfile"
done < <(find "$OVERRIDES_DIR" -type f -print0)

echo "Applying ConfigMap..."
# Use oc if present else kubectl
if command -v oc >/dev/null 2>&1; then
  oc apply -f "$tmpfile"
else
  kubectl apply -f "$tmpfile"
fi

echo "Done. Mounted at /app/config/overrides when chart installed with configOverrides.enabled=true."
rm "$tmpfile"
