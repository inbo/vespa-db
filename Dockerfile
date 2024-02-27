# syntax=docker/dockerfile:1
ARG PYTHON_VERSION=3.11.6
FROM python:$PYTHON_VERSION-slim AS base

LABEL org.opencontainers.image.description "monitoring vespa nests"

ENV PYTHONFAULTHANDLER 1
ENV PYTHONUNBUFFERED 1

# Install Poetry.
ENV POETRY_VERSION 1.7.1
RUN --mount=type=cache,target=/root/.cache/pip/ \
    pip install poetry==$POETRY_VERSION

# Install curl, compilers, and GDAL dependencies.
RUN rm /etc/apt/apt.conf.d/docker-clean
RUN --mount=type=cache,target=/var/cache/apt/ \
    --mount=type=cache,target=/var/lib/apt/ \
    apt-get update && apt-get install --no-install-recommends --yes curl build-essential gdal-bin libgdal-dev

# Configure GDAL environment variables, adjust according to the installed GDAL version
ENV GDAL_LIBRARY_PATH /usr/lib/libgdal.so
ENV GEOS_LIBRARY_PATH /usr/lib/libgeos_c.so

# Create and activate a virtual environment.
RUN python -m venv /opt/vespadb-env
ENV PATH /opt/vespadb-env/bin:$PATH
ENV VIRTUAL_ENV /opt/vespadb-env

WORKDIR /workspaces/vespadb/

RUN mkdir -p /root/.cache/pypoetry/ && mkdir -p /root/.config/pypoetry/ && \
    mkdir -p src/vespadb/ && touch src/vespadb/__init__.py && touch README.md

FROM base AS dev

# Install DevContainer utilities: zsh, git, and starship prompt. Note: Docker CLI setup has been updated.
RUN --mount=type=cache,target=/var/cache/apt/ \
    --mount=type=cache,target=/var/lib/apt/ \
    apt-get update && apt-get install --yes --no-install-recommends openssh-client git zsh gnupg lsb-release

# Setup Docker repository and install Docker CLI
RUN curl -fsSL https://download.docker.com/linux/debian/gpg | gpg --dearmor -o /usr/share/keyrings/docker-archive-keyring.gpg && \
    echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/docker-archive-keyring.gpg] https://download.docker.com/linux/debian $(lsb_release -cs) stable" | tee /etc/apt/sources.list.d/docker.list > /dev/null && \
    apt-get update && apt-get install --yes --no-install-recommends docker-ce-cli

# Install starship prompt and configure Git
RUN sh -c "$(curl -fsSL https://starship.rs/install.sh)" -- "--yes" && \
    git config --system --add safe.directory '*' && \
    echo 'eval "$(starship init zsh)"' >> ~/.zshrc \
    # Commented out to avoid build failure. Uncomment if poe-the-poet is installed and configured correctly.
    # && echo 'poe --help' >> ~/.zshrc \
    && zsh -c 'source ~/.zshrc'

CMD ["zsh"]

FROM base AS app

COPY poetry.lock* pyproject.toml /workspaces/vespadb/
RUN --mount=type=cache,target=/root/.cache/pypoetry/ \
    poetry install --only main --no-interaction --no-ansi

COPY . .
RUN chmod +x manage.py

ENTRYPOINT ["/opt/vespadb-env/bin/poe"]
CMD ["serve"]

ARG BUILD_BRANCH
ENV BUILD_BRANCH $BUILD_BRANCH
ARG BUILD_COMMIT
ENV BUILD_COMMIT $BUILD_COMMIT
ARG BUILD_TIMESTAMP
ENV BUILD_TIMESTAMP $BUILD_TIMESTAMP
