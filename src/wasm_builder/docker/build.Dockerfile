FROM ubuntu:24.04 AS wash-build-image

# Install dependencies and tools
RUN apt-get update && apt-get install -y \
    curl \
    wget \
    tar \
    git \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# ----------------- Install WasmCloud -----------------
RUN curl -s "https://packagecloud.io/install/repositories/wasmcloud/core/script.deb.sh" | bash && \
    apt-get install -y wash

# ----------------- Install Go 1.23.2 (match local) -----------------    
RUN wget https://go.dev/dl/go1.23.2.linux-amd64.tar.gz && \
    tar -C /usr/local -xzf go1.23.2.linux-amd64.tar.gz && \
    rm go1.23.2.linux-amd64.tar.gz

# Set Go environment variables
ENV PATH="/usr/local/go/bin:${PATH}"
ENV GOPATH="/go"
ENV GOROOT="/usr/local/go"

# ----------------- Install TinyGo 0.34.0 -----------------
RUN wget https://github.com/tinygo-org/tinygo/releases/download/v0.34.0/tinygo_0.34.0_amd64.deb && \
    dpkg -i tinygo_0.34.0_amd64.deb && \
    rm tinygo_0.34.0_amd64.deb

# ----------------- Install Rust & wasm-tools (match local version) -----------------
RUN curl https://sh.rustup.rs -sSf | sh -s -- -y && \
    . "$HOME/.cargo/env" && \
    cargo install --locked --version 1.222.0 wasm-tools

# Set Rust environment variables
ENV PATH="/root/.cargo/bin:${PATH}"

# Verify installations
RUN go version && tinygo version && cargo --version && wash --version && wasm-tools --version


# ----------------- Build the WasmCloud module -----------------
FROM wash-build-image

RUN mkdir /app
WORKDIR /app

# Install go dependencies, build the wasm module, push it to the registry
CMD ["sh", "-c", "\
set -e; \
echo 'Setting Go flags...'; \
go env -w GOFLAGS=-buildvcs=false; \
echo 'Downloading dependencies...'; \
go mod download; \
echo 'Tidying modules...'; \
go mod tidy; \
echo 'Resolving missing dependencies...'; \
go get github.com/bytecodealliance/wasm-tools-go/internal/go/gen@v0.3.2 || true; \
go get github.com/bytecodealliance/wasm-tools-go/internal/oci@v0.3.2 || true; \
go get github.com/bytecodealliance/wasm-tools-go/wit@v0.3.2 || true; \
go get github.com/bytecodealliance/wasm-tools-go/cmd/wit-bindgen-go@v0.3.2 || true; \
go mod tidy; \
echo 'Building WASM component...'; \
wash build; \
echo 'Build completed successfully!'; \
if [ -n \"$REGISTRY\" ]; then \
  echo \"Pushing to registry: $REGISTRY\"; \
  wash push \"$REGISTRY\" \"build/${COMPONENT_NAME}.wasm\"; \
  echo 'Push completed!'; \
else \
  echo 'Skipping push (no REGISTRY set)'; \
fi; \
echo 'Setting file permissions...'; \
chown -R \"${HOST_UID:-1000}:${HOST_GID:-1000}\" . 2>/dev/null || true; \
echo 'All done!' \
"]