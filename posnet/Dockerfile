FROM node:20-bullseye

# node:20-bullseye = Debian 11 = GLIBC 2.31 (posnet binaries require >= 2.31 — OK)
# Debian 11 has wkhtmltopdf in repos (Debian 12 removed it) — needed for simulator.
# DO NOT use node:*-alpine — Alpine uses musl libc, posnet .so files require glibc.
# Node >=18 <22 is required by posnetserver package.json engines field.

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        jq \
        python3 \
        make \
        g++ \
        wkhtmltopdf \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /opt/posnet

# This COPY will fail at build time if the file is missing — intentional.
# Place posnetserver.x64.5.7-GLIBC-2.31.1201.tar.gz in the posnet/ directory
# before running: docker compose build
COPY posnetserver.x64.5.7-GLIBC-2.31.1201.tar.gz .

RUN tar -xzf posnetserver.x64.5.7-GLIBC-2.31.1201.tar.gz \
    && rm posnetserver.x64.5.7-GLIBC-2.31.1201.tar.gz \
    && npm install

EXPOSE 3020 3021

# Mirrors what serverstart.sh does: set lib paths, then start the server.
# Serial port configuration from serverstart.sh is intentionally skipped
# (not needed for eth/tunnel connection types used in Docker).
CMD ["sh", "-c", "export POSNET_LIB_SHARE_DIR=$(pwd)/ && export LD_LIBRARY_PATH=$(pwd) && npm start"]
