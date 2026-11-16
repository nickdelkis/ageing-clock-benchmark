# Small, self-contained environment for the clock benchmark.
# Everything the analysis touches lives in the project folder, mounted at /work.
FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Run as a normal user. On Linux, pass your own UID/GID so files written
# into the mounted folder belong to you (see README).
ARG UID=1000
ARG GID=1000
RUN groupadd -g "${GID}" app && useradd -m -u "${UID}" -g "${GID}" app

RUN pip install torch --index-url https://download.pytorch.org/whl/cpu
COPY requirements.txt /tmp/requirements.txt
RUN pip install -r /tmp/requirements.txt && rm /tmp/requirements.txt

USER app
WORKDIR /work

# HOME points into the mounted project folder, so Biolearn's download cache
# and Jupyter settings persist between runs and never touch your real home.
ENV HOME=/work/.home \
    MPLCONFIGDIR=/work/.home/.matplotlib

CMD ["sh", "-c", "mkdir -p \"$HOME\" && exec jupyter lab --ip=0.0.0.0 --port=8888 --no-browser --notebook-dir=/work"]
