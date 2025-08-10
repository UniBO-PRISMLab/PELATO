// //go:generate go run github.com/bytecodealliance/wasm-tools-go/cmd/wit-bindgen-go generate --world default --out gen ./wit
package main

import (
	"fmt"
	"runtime/debug"
	"time"
	"encoding/json"

	store "github.com/UniBO-PRISMLab/PELATO/src/code_generator/templates/nats_to_nats-kv/gen/wasi/keyvalue/store"
	logger "github.com/UniBO-PRISMLab/PELATO/src/code_generator/templates/nats_to_nats-kv/gen/wasi/logging/logging"
	handler "github.com/UniBO-PRISMLab/PELATO/src/code_generator/templates/nats_to_nats-kv/gen/wasmcloud/messaging/handler"
	types "github.com/UniBO-PRISMLab/PELATO/src/code_generator/templates/nats_to_nats-kv/gen/wasmcloud/messaging/types"
	"github.com/bytecodealliance/wasm-tools-go/cm"
	gcm "go.bytecodealliance.org/cm"
)
// Simple structured logging helper
func logf(level logger.Level, msg string, kv ...string) {
	if len(kv) > 0 {
		msg = msg + " | " + fmt.Sprint(kv)
	}
	logger.Log(level, "KVWriter", msg)
}

type Message struct {
    Key  string
	Data string
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

	body := msg.Body
	message := Message{}

	// Unmarshal the message body into our struct
	if err := json.Unmarshal(body.Slice(), &message); err != nil {
		logf(logger.LevelError, "unmarshal message failed", "subject", msg.Subject, "error", err.Error())
		return cm.Err[cm.Result[string, struct{}, string]]("unmarshal error: " + err.Error())
	}

	if message.Data == "" {
		logf(logger.LevelWarn, "invalid message - skipped", "subject", msg.Subject)
		return cm.Err[cm.Result[string, struct{}, string]]("invalid message")
	}

	// if key is missing put topic in key
	if message.Key == "" {
		message.Key = msg.Subject
	}

	setRes := store.Bucket.Set(*kvStore.OK(), message.Key, gcm.ToList([]byte(message.Data)))
	if setRes.IsErr() {
		logf(logger.LevelError, "kv set failed", "subject", msg.Subject, "error", setRes.Err().String())
		return cm.Err[cm.Result[string, struct{}, string]]("kv set error: " + setRes.Err().String())
	}

	logf(logger.LevelInfo, "stored message", "key", message.Key, "bytes", fmt.Sprintf("%d", len(message.Data)), "duration", time.Since(start).String())
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
