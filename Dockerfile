ARG REGISTRY=ghcr.io
FROM ${REGISTRY}/senaite:2.x

USER root

# Install Python dependencies for senaite.hgumba
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

RUN pip install --no-deps \
    numpy==1.16.6 \
    Pillow \
    matplotlib==2.2.5 \
    reportlab \
    archetypes.schemaextender \
    cycler \
    kiwisolver \
    pyparsing==2.4.7 \
    python-dateutil \
    six \
    pytz \
    backports.functools-lru-cache \
    subprocess32 \
    psycopg2-binary==2.8.6

# Add .pth file for addon import
RUN echo "/opt/senaite/addons/src" > /usr/local/lib/python2.7/site-packages/senaite-hgumba.pth

# Copy package-includes into image (avoid bind mount permission issues)
RUN mkdir -p /home/senaite/senaitelims/parts/instance/etc/package-includes
COPY customizations/package-includes/050-senaite-hgumba-configure.zcml \
     /home/senaite/senaitelims/parts/instance/etc/package-includes/050-senaite-hgumba-configure.zcml

# Patch entrypoint: tolerate chown errors on Docker Desktop bind mounts
COPY customizations/patch-entrypoint.py /tmp/patch-entrypoint.py
RUN python /tmp/patch-entrypoint.py
