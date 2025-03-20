FROM mcr.microsoft.com/devcontainers/python:3.12

# Install uv
RUN curl -sSf https://astral.sh/uv/install.sh | sh

# Install additional packages
RUN apt-get update && export DEBIAN_FRONTEND=noninteractive \
    && apt-get -y install --no-install-recommends \
    postgresql-client \
    redis-tools \
    curl \
    jq \
    && apt-get clean -y && rm -rf /var/lib/apt/lists/*

# Set up a non-root user
ARG USERNAME=vscode
ARG USER_UID=1000
ARG USER_GID=$USER_UID

# Create the user
RUN groupadd --gid $USER_GID $USERNAME \
    && useradd --uid $USER_UID --gid $USER_GID -m $USERNAME \
    && apt-get update \
    && apt-get install -y sudo \
    && echo $USERNAME ALL=\(root\) NOPASSWD:ALL > /etc/sudoers.d/$USERNAME \
    && chmod 0440 /etc/sudoers.d/$USERNAME

# Add uv to PATH for all users
ENV PATH="/root/.cargo/bin:${PATH}"

# Set the default user
USER $USERNAME

# Add user's .local/bin to PATH
ENV PATH="/home/${USERNAME}/.local/bin:${PATH}"
