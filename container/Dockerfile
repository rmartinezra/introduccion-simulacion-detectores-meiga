ARG BASE_IMAGE=meiga_school:3.0
FROM ${BASE_IMAGE}

LABEL org.opencontainers.image.title="MEIGA School"
LABEL org.opencontainers.image.version="3.1"
LABEL org.opencontainers.image.description="MEIGA teaching image with self-contained WCD 30 s and 5 min fluxes"

RUN mkdir -p /opt/meiga-school/data
COPY experiments/wcd/flux-30s/input/bga_30s.shw /opt/meiga-school/data/bga_30s.shw
COPY experiments/wcd/bariloche-5min/input/bariloche_5min.shw /opt/meiga-school/data/bariloche_5min.shw
COPY experiments/wcd/flux-30s /opt/meiga-school/campaigns/wcd-flux-30s
COPY experiments/wcd/bariloche-5min /opt/meiga-school/campaigns/wcd-bariloche-5min

RUN sha256sum /opt/meiga-school/data/bariloche_5min.shw | \
    grep -qi '^db4f9e09a2b43898faffc7fea3446cba072777ff3cf9bb6ebe79296da56ced66 '
