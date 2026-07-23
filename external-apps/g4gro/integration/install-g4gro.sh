#!/usr/bin/env bash
set -Eeuo pipefail

readonly PREFIX="/opt/meiga-school/external/G4GROSimulator"
readonly VENDOR_DIR="$PREFIX/vendor"
readonly SOURCE_DIR="$PREFIX/meiga-source"
readonly BUILD_DIR="$PREFIX/build"
readonly RUNTIME_DIR="$PREFIX/runtime"
readonly RUNS_DIR="$PREFIX/runs"
readonly BASE_SOURCE="/opt/meiga-school/G4WCDSimulator/source"
readonly INTEGRATION_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
readonly ARCHIVE="${1:-/tmp/g4gro/Escuela.tar.gz}"
readonly BUILD_JOBS="${BUILD_JOBS:-2}"
readonly EXPECTED_ARCHIVE_SHA256="e8e2793fadc6ad2f25783cc075e9c66c2f21e940d251e24838baf4f306820900"

[[ "$BUILD_JOBS" =~ ^[1-9][0-9]*$ ]] || {
  echo "[ERROR] BUILD_JOBS must be a positive integer" >&2
  exit 2
}

for command_name in cmake g++ make patch sha256sum tar; do
  command -v "$command_name" >/dev/null || {
    echo "[ERROR] Missing build command: $command_name" >&2
    exit 1
  }
done

[[ -f "$ARCHIVE" ]] || {
  echo "[ERROR] Missing original G4GRO archive: $ARCHIVE" >&2
  exit 1
}
[[ -d "$BASE_SOURCE" ]] || {
  echo "[ERROR] Missing MEIGA base source: $BASE_SOURCE" >&2
  exit 1
}

echo "$EXPECTED_ARCHIVE_SHA256  $ARCHIVE" | sha256sum --check --strict

mkdir -p "$PREFIX" "$VENDOR_DIR" "$RUNTIME_DIR" "$RUNS_DIR"
tar -xzf "$ARCHIVE" -C "$VENDOR_DIR"

[[ -d "$VENDOR_DIR/Escuela/G4GROSimulator" ]] || {
  echo "[ERROR] The archive does not contain Escuela/G4GROSimulator" >&2
  exit 1
}

find "$VENDOR_DIR/Escuela" -type f -print0 \
  | sort -z \
  | xargs -0 sha256sum > "$PREFIX/original-files.sha256"
chmod -R a-w "$VENDOR_DIR"

cp -a "$BASE_SOURCE" "$SOURCE_DIR"
rm -rf "$SOURCE_DIR/.git"
cp -a "$VENDOR_DIR/Escuela/G4GROSimulator" \
  "$SOURCE_DIR/Applications/G4GROSimulator"
install -m 0644 "$VENDOR_DIR/Escuela/G4MPhysicsList.cc" \
  "$SOURCE_DIR/G4Models/G4MPhysicsList.cc"
install -m 0644 "$VENDOR_DIR/Escuela/Materials.cc" \
  "$SOURCE_DIR/G4Models/Materials.cc"

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
