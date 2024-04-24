# FRONTEND DEPLOYMENT
# First stage: Install Node.js and build the Vue.js project
FROM node:lts AS build-stage

# Set the working directory
WORKDIR /app
# Copy frontend package files to the working directory
COPY ./frontend/package*.json ./

# Install dependencies
RUN npm install

COPY ./frontend/ .

# Execute build
RUN npm run build 

FROM nginx:stable-alpine as frontend-prod
COPY default.conf /etc/nginx/conf.d/default.conf
COPY --from=build-stage /app/dist /usr/share/nginx/html
RUN nginx -t
EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]

# BACKEND DEPLOYMENT
# Base stage for the Python environment
FROM python:3.11.6-slim AS base

LABEL org.opencontainers.image.description "Monitoring Vespa observations"

ENV PYTHONFAULTHANDLER=1 \
    PYTHONUNBUFFERED=1 \
    POETRY_VERSION=1.7.1

# Install Poetry, Poe the Poet, and pre-commit
RUN --mount=type=cache,target=/root/.cache/pip/ \
    pip install poetry==$POETRY_VERSION poethepoet pre-commit

# Install curl, compilers, GDAL dependencies, and PostgreSQL client
RUN rm /etc/apt/apt.conf.d/docker-clean
RUN --mount=type=cache,target=/var/cache/apt/ \
    --mount=type=cache,target=/var/lib/apt/ \
    apt-get update && apt-get install --no-install-recommends --yes curl build-essential gdal-bin libgdal-dev postgresql-client

# Configure GDAL environment variables, adjust according to the installed GDAL version
ENV GDAL_LIBRARY_PATH /usr/lib/libgdal.so
ENV GEOS_LIBRARY_PATH /usr/lib/libgeos_c.so

# Create and activate a virtual environment
RUN python -m venv /opt/vespadb-env
ENV PATH /opt/vespadb-env/bin:$PATH
ENV VIRTUAL_ENV /opt/vespadb-env

WORKDIR /workspaces/vespadb/

RUN mkdir -p /root/.cache/pypoetry/ && mkdir -p /root/.config/pypoetry/ && \
    mkdir -p src/vespadb/ && touch src/vespadb/__init__.py && touch README.md

# Development stage setup
FROM base AS dev

# Install DevContainer utilities: zsh, git, and starship prompt. Note: Docker CLI setup has been updated
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
    && zsh -c 'source ~/.zshrc'

# Copy poetry and project configuration files to the container
COPY poetry.lock* pyproject.toml /workspaces/vespadb/

# Install the project dependencies - make sure to use the virtual environment
RUN poetry install --no-root --no-interaction --no-ansi

ENTRYPOINT ["/opt/vespadb-env/bin/poe"]
CMD ["serve"]

# Application stage setup
FROM base AS app

COPY poetry.lock* pyproject.toml /workspaces/vespadb/
RUN --mount=type=cache,target=/root/.cache/pypoetry/ \
    poetry install --only main --no-interaction --no-ansi

COPY . .

ENTRYPOINT ["/opt/vespadb-env/bin/poe"]
CMD ["serve"]

ARG BUILD_BRANCH
ENV BUILD_BRANCH $BUILD_BRANCH
ARG BUILD_COMMIT
ENV BUILD_COMMIT $BUILD_COMMIT
ARG BUILD_TIMESTAMP
ENV BUILD_TIMESTAMP $BUILD_TIMESTAMP