#pragma once
#include <Arduino.h>

// Lightweight reusable serial command handler.
// Reads lines terminated by '\n' and buffers them for the caller.
class SerialHandler {
  public:
    SerialHandler();
    // Called after Serial.begin(...) to initialize internal state
    void begin();

    // Must be called frequently to poll Serial and build lines
    void poll();

    // Returns true if a full line/command is available
    bool hasCommand();

    // Returns the next available command (without trailing newline).
    // Call only if hasCommand() returned true.
    String getCommand();

    // Send a text response back over Serial (adds newline)
    void sendResponse(const String &text);

  private:
    String _buffer;
    bool _complete;
};
