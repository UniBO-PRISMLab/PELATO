FROM golang:1.24-bullseye

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    wget \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Install Rust and Cargo
RUN curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh -s -- -y
ENV PATH="/root/.cargo/bin:${PATH}"

# Install wasm-tools (specific version)
RUN cargo install --locked wasm-tools@1.225.0

# Install TinyGodocker build -t wasmcloud-go .
RUN wget https://github.com/tinygo-org/tinygo/releases/download/v0.32.0/tinygo_0.32.0_amd64.deb \
    && dpkg -i tinygo_0.32.0_amd64.deb \
    && rm tinygo_0.32.0_amd64.deb

# Install wash
RUN curl -s https://packagecloud.io/install/repositories/wasmcloud/core/script.deb.sh | bash \
    && apt install wash

# Install wit-bindgen-go
RUN go install go.bytecodealliance.org/cmd/wit-bindgen-go@latest || \
    go install github.com/bytecodealliance/wasm-tools-go/cmd/wit-bindgen-go@latest || \
    go install github.com/ydnar/wasm-tools-go/cmd/wit-bindgen-go@latest


# Set up working directory
WORKDIR /workspace

# Copy project files
COPY . .

# Set environment variables
ENV PATH="/root/.wash:$PATH"
ENV GOPATH="/go"
ENV PATH="$GOPATH/bin:$PATH"