# Isolated G4GRO integration

This directory contains the original compressed package and the isolated
integration artifacts. The colleague's application is kept byte-for-byte under
the container's `vendor/Escuela` directory. It is not edited.

The isolated build uses:

- a private copy of the MEIGA source tree;
- the original `Materials.cc` and `G4MPhysicsList.cc` supplied in the archive;
- a small header-only compatibility patch declaring the supplied soil and
  brine materials;
- a localized serial run-manager selection because the supplied application
  registers its Geant4 user actions through the sequential interface;
- a private fix to the copied MEIGA configuration template so its generated
  header exposes the explicit Tyvek setting required by the teaching tree;
- a separate CMake build directory and runtime directory.

No file under `/opt/meiga-dev-source`, `/opt/meiga-dev-build`, or the three
course simulators is changed.

## Container layout

```text
/opt/meiga-school/external/G4GROSimulator/
├── vendor/Escuela/       original package, read-only
├── meiga-source/         private MEIGA source copy plus integration shims
├── build/                private CMake build
├── runtime/              integration configuration
├── runs/                 self-contained run directories
└── run-g4gro.sh          student-facing launcher
```

## Use

```bash
docker exec meiga_school \
  /opt/meiga-school/external/G4GROSimulator/run-g4gro.sh smoke my-test
```

Modes:

- `smoke`: three neutrons from the original `all_neutrons.shw`;
- `muon`: the original one-particle `vertical_muon.txt`;
- `practice`: the original 1,000-particle `practica.shw`;
- `full`: the original 39,832-particle `bga_30_segundos.shw`.

## Edit and rebuild G4GRO

Edit only the private working copy under `meiga-source`. Do not edit
`vendor/Escuela`: it is the read-only, byte-for-byte copy of the colleague's
original package.

Open a shell in the running container:

```bash
docker exec -it meiga_school bash
```

The main editable locations are:

```text
/opt/meiga-school/external/G4GROSimulator/meiga-source/
├── Applications/G4GROSimulator/   application .cc and .h files
└── G4Models/
    ├── G4MPhysicsList.cc           private physics-list copy
    └── Materials.cc                private materials copy
```

After changing an existing `.cc` or `.h` file, rebuild only G4GRO:

```bash
cmake --build /opt/meiga-school/external/G4GROSimulator/build \
  --target G4GROSimulator \
  --parallel "$(nproc)"
```

If files were added, removed, or a `CMakeLists.txt` was changed, configure the
private build again before compiling:

```bash
cmake \
  -S /opt/meiga-school/external/G4GROSimulator/meiga-source \
  -B /opt/meiga-school/external/G4GROSimulator/build

cmake --build /opt/meiga-school/external/G4GROSimulator/build \
  --target G4GROSimulator \
  --parallel "$(nproc)"
```

The rebuilt executable is written to:

```text
/opt/meiga-school/external/G4GROSimulator/build/Applications/G4GROSimulator/G4GROSimulator
```

Run the short validation after each rebuild:

```bash
/opt/meiga-school/external/G4GROSimulator/run-g4gro.sh \
  smoke rebuild-check
```

Changes made inside a container remain in that container but are lost if the
container is removed. Keep important source changes on the host (or in Git)
and copy or mount them into `meiga-source` before rebuilding.

The application currently emits two non-fatal Geant4 warnings inherited from
the supplied code: an overlap check for `Detectoruno` and a duplicated
radioactive-decay process. The smoke run still reaches “Simulation ended
successfully” and writes all three events. These warnings were not suppressed
because doing so would require changing the colleague's application or physics.
