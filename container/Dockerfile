ARG BASE_IMAGE=meiga_school:3.0
FROM ${BASE_IMAGE}

LABEL org.opencontainers.image.title="MEIGA School"
LABEL org.opencontainers.image.version="3.2"
LABEL org.opencontainers.image.description="MEIGA teaching image with self-contained WCD campaigns and isolated G4GRO"

RUN mkdir -p /opt/meiga-school/data
COPY experiments/wcd/flux-30s/input/bga_30s.shw /opt/meiga-school/data/bga_30s.shw
COPY experiments/wcd/bariloche-5min/input/bariloche_5min.shw /opt/meiga-school/data/bariloche_5min.shw
COPY experiments/wcd/flux-30s /opt/meiga-school/campaigns/wcd-flux-30s
COPY experiments/wcd/bariloche-5min /opt/meiga-school/campaigns/wcd-bariloche-5min
COPY external-apps/g4gro /tmp/g4gro

RUN sha256sum /opt/meiga-school/data/bariloche_5min.shw | \
    grep -qi '^db4f9e09a2b43898faffc7fea3446cba072777ff3cf9bb6ebe79296da56ced66 ' && \
    bash /tmp/g4gro/integration/install-g4gro.sh \
      /tmp/g4gro/original/Escuela.tar.gz && \
    rm -rf /tmp/g4gro
