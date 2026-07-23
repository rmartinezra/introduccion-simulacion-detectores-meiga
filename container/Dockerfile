FROM ubuntu:22.04

ARG DEBIAN_FRONTEND=noninteractive
ARG GEANT4_VERSION=10.7.4
ARG GEANT4_SOURCE_SHA256=602b41dfee1fa6b33b026d00c5bd940155d7e5d0b3495230a87e2a25b28f9996
ARG BUILD_JOBS=2

LABEL org.opencontainers.image.title="MEIGA School"
LABEL org.opencontainers.image.version="3.3"
LABEL org.opencontainers.image.description="Self-contained MEIGA detector course with Geant4 10.7.4, WCD campaigns and isolated G4GRO"
LABEL org.opencontainers.image.source="https://github.com/rmartinezra/introduccion-simulacion-detectores-meiga"

SHELL ["/bin/bash", "-o", "pipefail", "-c"]

RUN apt-get update && \
    apt-get install -y --no-install-recommends \
      build-essential \
      ca-certificates \
      cmake \
      curl \
      libboost-filesystem-dev \
      libboost-iostreams-dev \
      libboost-system-dev \
      libexpat1-dev \
      libgl1-mesa-dev \
      libglu1-mesa-dev \
      libx11-dev \
      libxerces-c-dev \
      libxi-dev \
      libxmu-dev \
      ninja-build \
      patch \
      zlib1g-dev && \
    rm -rf /var/lib/apt/lists/*

ENV GEANT4_PREFIX=/opt/GEANT4/10.07.p04-install

RUN curl -LfsS \
      "https://github.com/Geant4/geant4/archive/refs/tags/v${GEANT4_VERSION}.tar.gz" \
      -o /tmp/geant4.tar.gz && \
    echo "${GEANT4_SOURCE_SHA256}  /tmp/geant4.tar.gz" \
      | sha256sum --check --strict && \
    tar -xzf /tmp/geant4.tar.gz -C /tmp && \
    cmake \
      -S "/tmp/geant4-${GEANT4_VERSION}" \
      -B /tmp/geant4-build \
      -G Ninja \
      -DCMAKE_BUILD_TYPE=Release \
      -DCMAKE_INSTALL_PREFIX="${GEANT4_PREFIX}" \
      -DGEANT4_BUILD_MULTITHREADED=ON \
      -DGEANT4_INSTALL_DATA=ON \
      -DGEANT4_INSTALL_EXAMPLES=OFF \
      -DGEANT4_USE_GDML=ON \
      -DGEANT4_USE_OPENGL_X11=ON \
      -DGEANT4_USE_SYSTEM_EXPAT=ON \
      -DGEANT4_USE_SYSTEM_ZLIB=ON && \
    if ! cmake --build /tmp/geant4-build --parallel "${BUILD_JOBS}" \
      >/tmp/geant4-build.log 2>&1; then \
        tail -n 120 /tmp/geant4-build.log; \
        exit 1; \
    fi && \
    tail -n 20 /tmp/geant4-build.log && \
    if ! cmake --install /tmp/geant4-build \
      >/tmp/geant4-install.log 2>&1; then \
        tail -n 120 /tmp/geant4-install.log; \
        exit 1; \
    fi && \
    tail -n 20 /tmp/geant4-install.log && \
    rm -rf \
      /tmp/geant4.tar.gz \
      "/tmp/geant4-${GEANT4_VERSION}" \
      /tmp/geant4-build \
      /tmp/geant4-build.log \
      /tmp/geant4-install.log

ENV PATH="${GEANT4_PREFIX}/bin:/opt/meiga-school/G4HodoscopeSimulator:/opt/meiga-school/G4TowSimulator:/opt/meiga-school/G4WCDSimulator:${PATH}"
ENV LD_LIBRARY_PATH="${GEANT4_PREFIX}/lib"
ENV G4NEUTRONHPDATA="${GEANT4_PREFIX}/share/Geant4-10.7.4/data/G4NDL4.6"
ENV G4LEDATA="${GEANT4_PREFIX}/share/Geant4-10.7.4/data/G4EMLOW7.13"
ENV G4LEVELGAMMADATA="${GEANT4_PREFIX}/share/Geant4-10.7.4/data/PhotonEvaporation5.7"
ENV G4RADIOACTIVEDATA="${GEANT4_PREFIX}/share/Geant4-10.7.4/data/RadioactiveDecay5.6"
ENV G4PARTICLEXSDATA="${GEANT4_PREFIX}/share/Geant4-10.7.4/data/G4PARTICLEXS3.1.1"
ENV G4PIIDATA="${GEANT4_PREFIX}/share/Geant4-10.7.4/data/G4PII1.3"
ENV G4REALSURFACEDATA="${GEANT4_PREFIX}/share/Geant4-10.7.4/data/RealSurface2.2"
ENV G4SAIDXSDATA="${GEANT4_PREFIX}/share/Geant4-10.7.4/data/G4SAIDDATA2.0"
ENV G4ABLADATA="${GEANT4_PREFIX}/share/Geant4-10.7.4/data/G4ABLA3.1"
ENV G4INCLDATA="${GEANT4_PREFIX}/share/Geant4-10.7.4/data/G4INCL1.0"
ENV G4ENSDFSTATEDATA="${GEANT4_PREFIX}/share/Geant4-10.7.4/data/G4ENSDFSTATE2.3"

COPY container/meiga-school-source.tar.gz /tmp/meiga-school-source.tar.gz
COPY container/install-meiga-school.sh /tmp/install-meiga-school.sh

RUN BUILD_JOBS="${BUILD_JOBS}" \
      bash /tmp/install-meiga-school.sh /tmp/meiga-school-source.tar.gz && \
    rm -f /tmp/install-meiga-school.sh /tmp/meiga-school-source.tar.gz

RUN mkdir -p /opt/meiga-school/data
COPY experiments/wcd/flux-30s/input/bga_30s.shw /opt/meiga-school/data/bga_30s.shw
COPY experiments/wcd/bariloche-5min/input/bariloche_5min.shw /opt/meiga-school/data/bariloche_5min.shw
COPY experiments/wcd/flux-30s /opt/meiga-school/campaigns/wcd-flux-30s
COPY experiments/wcd/bariloche-5min /opt/meiga-school/campaigns/wcd-bariloche-5min
COPY external-apps/g4gro /tmp/g4gro

RUN apt-get update && \
    apt-get install -y --no-install-recommends \
      less \
      nano \
      nlohmann-json3-dev \
      vim && \
    rm -rf /var/lib/apt/lists/* && \
    sha256sum /opt/meiga-school/data/bariloche_5min.shw | \
      grep -qi '^db4f9e09a2b43898faffc7fea3446cba072777ff3cf9bb6ebe79296da56ced66 ' && \
    BUILD_JOBS="${BUILD_JOBS}" \
      bash /tmp/g4gro/integration/install-g4gro.sh \
      /tmp/g4gro/original/Escuela.tar.gz && \
    rm -rf /tmp/g4gro

WORKDIR /workspace
ENTRYPOINT []
CMD ["sleep", "infinity"]
