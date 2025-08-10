// //go:generate go run github.com/bytecodealliance/wasm-tools-go/cmd/wit-bindgen-go generate --world default --out gen ./wit
package main

import (
	"fmt"
	"runtime/debug"
	"time"

	store "github.com/UniBO-PRISMLab/PELATO/src/code_generator/templates/nats_to_nats-kv/gen/wasi/keyvalue/store"
	logger "github.com/UniBO-PRISMLab/PELATO/src/code_generator/templates/nats_to_nats-kv/gen/wasi/logging/logging"
	"github.com/UniBO-PRISMLab/PELATO/src/code_generator/templates/nats_to_nats-kv/gen/wasmcloud/messaging/consumer"
	handler "github.com/UniBO-PRISMLab/PELATO/src/code_generator/templates/nats_to_nats-kv/gen/wasmcloud/messaging/handler"
	types "github.com/UniBO-PRISMLab/PELATO/src/code_generator/templates/nats_to_nats-kv/gen/wasmcloud/messaging/types"
	"github.com/bytecodealliance/wasm-tools-go/cm"
)
// Simple structured logging helper
func logf(level logger.Level, msg string, kv ...string) {
	if len(kv) > 0 {
		msg = msg + " | " + fmt.Sprint(kv)
	}
	logger.Log(level, "KVWriter", msg)
}

func init() { handler.Exports.HandleMessage = handleMessage }

// handleMessage: on each received message we write its body to the keyvalue bucket
// using the message subject as the key. No reply/publish, just persistence.
func handleMessage(msg types.BrokerMessage) cm.Result[string, struct{}, string] {
	start := time.Now()
	logf(logger.LevelInfo, "received message", "subject", msg.Subject, "len", fmt.Sprintf("%d", msg.Body.Len()))

	if msg.Body.Len() == 0 {
		logf(logger.LevelWarn, "empty body - skipped", "subject", msg.Subject)
		return cm.Err[cm.Result[string, struct{}, string]]("empty body")
	}

	// Open bucket
	kvStore := store.Open("default")
	if err := kvStore.Err(); err != nil {
		logf(logger.LevelError, "open bucket failed", "error", err.String())
		return cm.Err[cm.Result[string, struct{}, string]]("kv open error: " + err.String())
	}

	// Extract raw body bytes
	body := msg.Body
	// Copy body into a Go byte slice
	bytes := make([]byte, body.Len())
	for i := uint32(0); i < body.Len(); i++ {
		bytes[i] = *body.Data().Add(i)
	}

	// Use message subject as key (simple strategy). Alternative strategies could parse JSON.
	key := msg.Subject
	setRes := store.Bucket.Set(*kvStore.OK(), key, cm.ToList(bytes))
	if setRes.IsErr() {
		logf(logger.LevelError, "kv set failed", "subject", msg.Subject, "error", setRes.Err().String())
		return cm.Err[cm.Result[string, struct{}, string]]("kv set error: " + setRes.Err().String())
	}

	logf(logger.LevelInfo, "stored message", "key", key, "bytes", fmt.Sprintf("%d", len(bytes)), "duration", time.Since(start).String())
	return cm.OK[cm.Result[string, struct{}, string]](struct{}{})
}

// Defensive empty main
func main() {
	// All logic handled via messaging handler.
	defer func() {
		if r := recover(); r != nil {
			logf(logger.LevelError, "panic recovered in main", "panic", fmt.Sprint(r), "stack", string(debug.Stack()))
		}
	}()
}
