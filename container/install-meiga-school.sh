#!/usr/bin/env bash
set -Eeuo pipefail

readonly SOURCE_ARCHIVE="${1:-/tmp/meiga-school-source.tar.gz}"
readonly EXPECTED_SOURCE_SHA256="bb36423c377e2fffe604c693df4ce8849d0455ec498691f39ed1c1342d7367b2"
readonly SOURCE_DIR="/opt/meiga-dev-source"
readonly BUILD_DIR="/opt/meiga-dev-build"
readonly SCHOOL_DIR="/opt/meiga-school"
readonly GEANT4_DIR="/opt/GEANT4/10.07.p04-install/lib/Geant4-10.7.4"
readonly BUILD_JOBS="${BUILD_JOBS:-2}"

[[ -f "$SOURCE_ARCHIVE" ]] || {
  echo "[ERROR] Missing MEIGA source archive: $SOURCE_ARCHIVE" >&2
  exit 1
}
echo "$EXPECTED_SOURCE_SHA256  $SOURCE_ARCHIVE" \
  | sha256sum --check --strict

mkdir -p "$SOURCE_DIR" "$BUILD_DIR" "$SCHOOL_DIR"
tar -xzf "$SOURCE_ARCHIVE" -C "$SOURCE_DIR"

# These applications register user actions directly on the run manager. Force
# Geant4's serial manager so the same source works with a multithreaded Geant4
# installation without the fatal Run0123 exception.
for app_name in G4HodoscopeSimulator G4TowSimulator G4WCDSimulator; do
  app_source="$SOURCE_DIR/Applications/$app_name/$app_name.cc"
  [[ -f "$app_source" ]] || {
    echo "[ERROR] Missing application source: $app_source" >&2
    exit 1
  }
  grep -Fq 'G4RunManagerFactory::CreateRunManager();' "$app_source" || {
    echo "[ERROR] Unexpected run-manager code in $app_source" >&2
    exit 1
  }
  sed -i \
    's/G4RunManagerFactory::CreateRunManager();/G4RunManagerFactory::CreateRunManager(G4RunManagerType::Serial);/' \
    "$app_source"
done

cmake \
  -S "$SOURCE_DIR" \
  -B "$BUILD_DIR" \
  -DGeant4_DIR="$GEANT4_DIR" \
  -DWITH_GEANT4_UIVIS=ON \
  -DCMAKE_BUILD_TYPE=Release
cmake --build "$BUILD_DIR" \
  --target G4HodoscopeSimulator G4TowSimulator G4WCDSimulator \
  --parallel "$BUILD_JOBS"

assemble_app() {
  local app_name="$1"
  local sample_file="$2"
  local app_source="$SOURCE_DIR/Applications/$app_name"
  local app_build="$BUILD_DIR/Applications/$app_name"
  local destination="$SCHOOL_DIR/$app_name"

  for required_file in \
    "$app_build/$app_name" \
    "$app_source/$app_name.json" \
    "$app_source/DetectorList.xml" \
    "$app_source/DetectorProperties.xml" \
    "$app_source/SchoolMakefile" \
    "$SOURCE_DIR/CONFIGURATION-SCHOOL.md" \
    "$sample_file"; do
    [[ -f "$required_file" ]] || {
      echo "[ERROR] Missing required file: $required_file" >&2
      exit 1
    }
  done

  mkdir -p "$destination"
  install -m 0755 "$app_build/$app_name" "$destination/$app_name"
  install -m 0644 "$app_source/$app_name.json" \
    "$destination/$app_name.json"
  install -m 0644 "$app_source/DetectorList.xml" \
    "$destination/DetectorList.xml"
  install -m 0644 "$app_source/DetectorProperties.xml" \
    "$destination/DetectorProperties.xml"
  install -m 0644 "$app_source/SchoolMakefile" "$destination/Makefile"
  install -m 0644 "$SOURCE_DIR/CONFIGURATION-SCHOOL.md" \
    "$destination/CONFIGURATION.md"
  install -m 0644 "$sample_file" "$destination/$(basename "$sample_file")"

  cp "$destination/$app_name.json" "$destination/config-ecomug.json"
  cp "$destination/$app_name.json" "$destination/config-arti.json"
  sed -i 's/"UseEcoMug"/"UseARTI"/' "$destination/config-arti.json"
  cp -a "$SOURCE_DIR" "$destination/source"
}

assemble_app \
  G4HodoscopeSimulator \
  "$SOURCE_DIR/Applications/G4HodoscopeSimulator/vertical_muon.txt"
assemble_app \
  G4TowSimulator \
  "$SOURCE_DIR/Applications/G4TowSimulator/vertical_muon.txt"
assemble_app \
  G4WCDSimulator \
  "$SOURCE_DIR/Documentation/SampleFlux/salida_bga_30.shw"

test -x "$SCHOOL_DIR/G4HodoscopeSimulator/G4HodoscopeSimulator"
test -x "$SCHOOL_DIR/G4TowSimulator/G4TowSimulator"
test -x "$SCHOOL_DIR/G4WCDSimulator/G4WCDSimulator"
echo "[OK] MEIGA teaching applications installed in $SCHOOL_DIR"
