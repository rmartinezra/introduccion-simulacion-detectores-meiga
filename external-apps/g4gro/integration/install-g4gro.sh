#!/usr/bin/env bash
set -Eeuo pipefail

readonly PREFIX="/opt/meiga-school/external/G4GROSimulator"
readonly VENDOR_DIR="$PREFIX/vendor"
readonly LEGACY_VENDOR_DIR="$VENDOR_DIR/legacy"
readonly CURRENT_VENDOR_DIR="$VENDOR_DIR/current"
readonly SOURCE_DIR="$PREFIX/meiga-source"
readonly BUILD_DIR="$PREFIX/build"
readonly RUNTIME_DIR="$PREFIX/runtime"
readonly RUNS_DIR="$PREFIX/runs"
readonly BASE_SOURCE="/opt/meiga-school/G4WCDSimulator/source"
readonly INTEGRATION_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
readonly LEGACY_ARCHIVE="${1:-/tmp/g4gro/Escuela.tar.gz}"
readonly CURRENT_ARCHIVE="${2:-/tmp/g4gro/G4GROSimulator.zip}"
readonly BUILD_JOBS="${BUILD_JOBS:-2}"
readonly EXPECTED_LEGACY_SHA256="e8e2793fadc6ad2f25783cc075e9c66c2f21e940d251e24838baf4f306820900"
readonly EXPECTED_CURRENT_SHA256="9ddfa1f41ce66ee7deaf837c2c420d7b290ce21d44d08fa10741f1b6f2971f68"

[[ "$BUILD_JOBS" =~ ^[1-9][0-9]*$ ]] || {
  echo "[ERROR] BUILD_JOBS must be a positive integer" >&2
  exit 2
}

for command_name in cmake g++ make patch sha256sum tar unzip; do
  command -v "$command_name" >/dev/null || {
    echo "[ERROR] Missing build command: $command_name" >&2
    exit 1
  }
done

[[ -f "$LEGACY_ARCHIVE" ]] || {
  echo "[ERROR] Missing legacy G4GRO archive: $LEGACY_ARCHIVE" >&2
  exit 1
}
[[ -f "$CURRENT_ARCHIVE" ]] || {
  echo "[ERROR] Missing current G4GRO archive: $CURRENT_ARCHIVE" >&2
  exit 1
}
[[ -d "$BASE_SOURCE" ]] || {
  echo "[ERROR] Missing MEIGA base source: $BASE_SOURCE" >&2
  exit 1
}

echo "$EXPECTED_LEGACY_SHA256  $LEGACY_ARCHIVE" | sha256sum --check --strict
echo "$EXPECTED_CURRENT_SHA256  $CURRENT_ARCHIVE" | sha256sum --check --strict

mkdir -p \
  "$PREFIX" \
  "$LEGACY_VENDOR_DIR" \
  "$CURRENT_VENDOR_DIR" \
  "$RUNTIME_DIR" \
  "$RUNS_DIR"
tar -xzf "$LEGACY_ARCHIVE" -C "$LEGACY_VENDOR_DIR"
unzip -q "$CURRENT_ARCHIVE" -d "$CURRENT_VENDOR_DIR"

[[ -d "$LEGACY_VENDOR_DIR/Escuela/G4GROSimulator" ]] || {
  echo "[ERROR] The legacy archive does not contain Escuela/G4GROSimulator" >&2
  exit 1
}
[[ -d "$CURRENT_VENDOR_DIR/G4GROSimulator" ]] || {
  echo "[ERROR] The current archive does not contain G4GROSimulator" >&2
  exit 1
}

find "$LEGACY_VENDOR_DIR/Escuela" -type f -print0 \
  | sort -z \
  | xargs -0 sha256sum > "$PREFIX/legacy-files.sha256"
find "$CURRENT_VENDOR_DIR/G4GROSimulator" -type f -print0 \
  | sort -z \
  | xargs -0 sha256sum > "$PREFIX/current-files.sha256"
chmod -R a-w "$VENDOR_DIR"

cp -a "$BASE_SOURCE" "$SOURCE_DIR"
rm -rf "$SOURCE_DIR/.git"
cp -a "$CURRENT_VENDOR_DIR/G4GROSimulator" \
  "$SOURCE_DIR/Applications/G4GROSimulator"
install -m 0644 "$LEGACY_VENDOR_DIR/Escuela/G4MPhysicsList.cc" \
  "$SOURCE_DIR/G4Models/G4MPhysicsList.cc"
install -m 0644 "$LEGACY_VENDOR_DIR/Escuela/Materials.cc" \
  "$SOURCE_DIR/G4Models/Materials.cc"
chmod -R u+w "$SOURCE_DIR"

patch --directory="$SOURCE_DIR" --strip=1 --batch \
  < "$INTEGRATION_DIR/meiga-isolation.patch"
patch --directory="$SOURCE_DIR" --strip=1 --batch \
  < "$INTEGRATION_DIR/meiga-base-template.patch"

install -m 0644 "$INTEGRATION_DIR/runtime-config.json" \
  "$RUNTIME_DIR/G4GROSimulator.json"
install -m 0644 "$INTEGRATION_DIR/DetectorProperties.xml" \
  "$RUNTIME_DIR/DetectorProperties.xml"
install -m 0755 "$INTEGRATION_DIR/run-g4gro.sh" \
  "$PREFIX/run-g4gro.sh"
install -m 0644 "$INTEGRATION_DIR/../README.md" \
  "$PREFIX/README.md"

cmake -S "$SOURCE_DIR" -B "$BUILD_DIR" -DCMAKE_BUILD_TYPE=Release
cmake --build "$BUILD_DIR" \
  --target G4GROSimulator \
  --parallel "$BUILD_JOBS"

test -x "$BUILD_DIR/Applications/G4GROSimulator/G4GROSimulator"
echo "[OK] Isolated G4GRO build installed at $PREFIX"
