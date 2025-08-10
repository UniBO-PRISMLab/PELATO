//go:generate go run github.com/bytecodealliance/wasm-tools-go/cmd/wit-bindgen-go generate --world hello --out gen ./wit
package main

import (
	"fmt"
	"runtime/debug"
	"time"
	logger "github.com/UniBO-PRISMLab/PELATO/src/code_generator/templates/processor_nats/gen/wasi/logging/logging"
	"github.com/UniBO-PRISMLab/PELATO/src/code_generator/templates/processor_nats/gen/wasmcloud/messaging/consumer"
	"github.com/UniBO-PRISMLab/PELATO/src/code_generator/templates/processor_nats/gen/wasmcloud/messaging/handler"
	"github.com/UniBO-PRISMLab/PELATO/src/code_generator/templates/processor_nats/gen/wasmcloud/messaging/types"
	"github.com/bytecodealliance/wasm-tools-go/cm"
)

// NOTE: helper logging
func logf(level logger.Level, msg string, kv ...string) {
	if len(kv) > 0 {
		msg = msg + " | " + fmt.Sprint(kv)
	}
	logger.Log(level, "MessageHandler", msg)
}

type messagingConsumerAdapter struct {
	Publish func(msg types.BrokerMessage) (result cm.Result[string, struct{}, string])
}

var messagingConsumer = &messagingConsumerAdapter{Publish: consumer.Publish}

func init() { handler.Exports.HandleMessage = handleMessage }

// Wrap exec_task with panic recovery
func safeExec(input string) (out string, failed bool) {
	start := time.Now()
	defer func() {
		if r := recover(); r != nil {
			failed = true
			logf(logger.LevelError, fmt.Sprintf("panic in task: %v", r), "duration", time.Since(start).String(), "stack", string(debug.Stack()))
		}
	}()
	out = exec_task(input) // provided by template/user
	logf(logger.LevelDebug, "task executed", "duration", time.Since(start).String())
	return
}

func handleMessage(msg types.BrokerMessage) cm.Result[string, struct{}, string] {
	start := time.Now()
	logf(logger.LevelInfo, "received message", "subject", msg.Subject, "len", fmt.Sprintf("%d", msg.Body.Len()))

	if msg.Body.Len() == 0 {
		logf(logger.LevelWarn, "empty body - skipping")
		return cm.Err[cm.Result[string, struct{}, string]]("empty body")
	}

	destTopic := "{{ dest_topic }}" // TODO: load from config

	arg := cm.LiftString[string, *uint8, uint8](msg.Body.Data(), uint8(msg.Body.Len()))
	result, failed := safeExec(arg)
	if failed {
		return cm.Err[cm.Result[string, struct{}, string]]("task panic")
	}

	reply := types.BrokerMessage{
		Subject: destTopic,
		Body:    cm.ToList([]byte(result)),
		ReplyTo: cm.None[string](),
	}

	pubRes := messagingConsumer.Publish(reply)
	if pubRes.IsErr() {
		errMsg := *pubRes.Err()
		logf(logger.LevelError, "publish failed", "error", errMsg, "duration", time.Since(start).String())
		return cm.Err[cm.Result[string, struct{}, string]]("publish failed: " + errMsg)
	}

	logf(logger.LevelInfo, "message processed", "duration", time.Since(start).String())
	return cm.OK[cm.Result[string, struct{}, string]](struct{}{})
}

func main() {}
