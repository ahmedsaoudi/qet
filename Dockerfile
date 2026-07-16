FROM python:3.11-slim-bookworm

# Update apt and install essential tools that qet might manage or use
RUN apt-get update && apt-get install -y \
    curl \
    sudo \
    wget \
    git \
    && rm -rf /var/lib/apt/lists/*

# Install uv globally
RUN pip install --no-cache-dir uv

# Add a non-root user for safe testing, but grant sudo without password
RUN useradd -m -s /bin/bash qetuser && \
    echo "qetuser ALL=(ALL) NOPASSWD:ALL" >> /etc/sudoers

# Switch to the new user
USER qetuser
WORKDIR /home/qetuser/app

# Copy the qet source code into the container
COPY --chown=qetuser:qetuser . .

# Create a virtual environment
RUN uv venv /home/qetuser/venv

# Activate the virtual environment
ENV VIRTUAL_ENV="/home/qetuser/venv"
ENV PATH="/home/qetuser/venv/bin:$PATH"

# Install qet into the active virtual environment using uv
RUN uv pip install -e .

# Define the entrypoint to run qet or open a bash shell
ENTRYPOINT ["/bin/bash"]
