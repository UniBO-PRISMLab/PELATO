## NATS -> KeyValue Writer

This component listens for messages from the wasmCloud messaging provider and, for every received message, writes the message body into the default key-value bucket using the subject as the key. It does not publish any response.

### Capabilities

- wasmcloud:messaging/handler (export) to receive messages
- wasi:keyvalue/store to persist data
- wasi:logging/logging for structured logs

### Build

```
wasm pack build
```

### Deploy (example with wash)

Ensure a messaging (NATS) and keyvalue provider are running and linked to the component with the handler interface exported.

### Behavior

1. Receive message (subject S, body B)
2. Open bucket `default`
3. Set key=S, value=B
4. Log success or error

Empty bodies are skipped with a warning.
