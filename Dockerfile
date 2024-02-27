# syntax=docker/dockerfile:1
ARG PYTHON_VERSION=3.11.6
FROM python:$PYTHON_VERSION-slim AS base

LABEL org.opencontainers.image.description "vespawatch"

# Configure Python to print tracebacks on crash [1], and to not buffer stdout and stderr [2].
# [1] https://docs.python.org/3/using/cmdline.html#envvar-PYTHONFAULTHANDLER
# [2] https://docs.python.org/3/using/cmdline.html#envvar-PYTHONUNBUFFERED
ENV PYTHONFAULTHANDLER 1
ENV PYTHONUNBUFFERED 1

# Install Poetry.
ENV POETRY_VERSION 1.7.1
RUN --mount=type=cache,target=/root/.cache/pip/ \
    pip install poetry==$POETRY_VERSION

# Install curl & compilers that may be required for certain packages or platforms.
# The stock ubuntu image cleans up /var/cache/apt automatically. This makes the build process slow.
# Enable apt caching by removing docker-clean
RUN rm /etc/apt/apt.conf.d/docker-clean
RUN --mount=type=cache,target=/var/cache/apt/ \
    --mount=type=cache,target=/var/lib/apt/ \
    apt-get update && apt-get install --no-install-recommends --yes curl build-essential gdal-bin libgdal-dev

# Create and activate a virtual environment.
RUN python -m venv /opt/vespadb-env
ENV PATH /opt/vespadb-env/bin:$PATH
ENV VIRTUAL_ENV /opt/vespadb-env

# Set the working directory.
WORKDIR /workspaces/vespadb/

# Touch minimal files to allow Poetry to install dependencies.
RUN mkdir -p /root/.cache/pypoetry/ && mkdir -p /root/.config/pypoetry/ && \
    mkdir -p src/vespadb/ && touch src/vespadb/__init__.py && touch README.md



FROM base AS dev

# Install DevContainer utilities: zsh, git, docker cli, starship prompt.
# Docker: only docker cli is installeed and not the entire engine.
RUN --mount=type=cache,target=/var/cache/apt/ \
    --mount=type=cache,target=/var/lib/apt/ \
    apt-get update && apt-get install --yes --no-install-recommends openssh-client git zsh gnupg  && \
    # Install docker cli (based on https://get.docker.com/)
    install -m 0755 -d /etc/apt/keyrings && \
    curl -fsSL "https://download.docker.com/linux/debian/gpg" | gpg --dearmor --yes -o /etc/apt/keyrings/docker.gpg && \
    chmod a+r /etc/apt/keyrings/docker.gpg && \
    apt_repo="deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/debian bookworm stable" && \
    echo "$apt_repo" > /etc/apt/sources.list.d/docker.list && \
    apt-get update && apt-get --yes --no-install-recommends install docker-ce-cli docker-compose-plugin && \
    # Install starship prompt
    sh -c "$(curl -fsSL https://starship.rs/install.sh)" -- "--yes" && \
    # Mark the workspace as safe for git
    git config --system --add safe.directory '*'

# Install the run time Python dependencies in the virtual environment.
COPY poetry.lock* pyproject.toml /workspaces/vespadb/
RUN --mount=type=cache,target=/root/.cache/pypoetry/ \
    poetry install --no-interaction --no-ansi

# Install pre-commit hooks & activate starship.
COPY .pre-commit-config.yaml /workspaces/vespadb/
RUN git init && pre-commit install --install-hooks && \
    echo 'eval "$(starship init zsh)"' >> ~/.zshrc && \
    echo 'poe --help' >> ~/.zshrc && \
    zsh -c 'source ~/.zshrc'

# Copy poetry and project configuration files to the container
COPY poetry.lock* pyproject.toml /workspaces/vespadb/

# Install the project dependencies - make sure to use the virtual environment
RUN poetry install --no-root --no-interaction --no-ansi

CMD ["zsh"]



FROM base AS app

# Install the run time Python dependencies in the virtual environment.
COPY poetry.lock* pyproject.toml /workspaces/vespadb/
RUN --mount=type=cache,target=/root/.cache/pypoetry/ \
    poetry install --only main --no-interaction --no-ansi

# Copy the package source code.
COPY . .

ENTRYPOINT ["/opt/vespadb-env/bin/poe"]
CMD ["serve"]

# Provide build information as environment variables.
ARG BUILD_BRANCH
ENV BUILD_BRANCH $BUILD_BRANCH
ARG BUILD_COMMIT
ENV BUILD_COMMIT $BUILD_COMMIT
ARG BUILD_TIMESTAMP
ENV BUILD_TIMESTAMP $BUILD_TIMESTAMP
