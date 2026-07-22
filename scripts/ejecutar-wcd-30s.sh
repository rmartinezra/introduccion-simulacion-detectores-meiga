#!/usr/bin/env bash
# Compatibilidad con el nombre usado en las primeras versiones del curso.
set -Eeuo pipefail
SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd -- "$SCRIPT_DIR/.." && pwd)"
exec "$SCRIPT_DIR/run-wcd-campaign.sh" \
  --experiment "$PROJECT_ROOT/experiments/wcd/flux-30s" "$@"
