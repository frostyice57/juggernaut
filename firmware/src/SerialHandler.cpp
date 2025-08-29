#include "SerialHandler.h"

SerialHandler::SerialHandler() : _buffer(), _complete(false) {}

void SerialHandler::begin() {
    _buffer = "";
    _complete = false;
}

void SerialHandler::poll() {
    while (Serial.available()) {
        char c = (char)Serial.read();
        if (c == '\n') {
            _complete = true;
            // strip any carriage returns
            while (_buffer.endsWith("\r")) _buffer.remove(_buffer.length() - 1);
            break;
        } else {
            _buffer += c;
        }
    }
}

bool SerialHandler::hasCommand() { return _complete; }

String SerialHandler::getCommand() {
    if (!_complete) return String();
    String cmd = _buffer;
    _buffer = "";
    _complete = false;
    cmd.trim();
    return cmd;
}

void SerialHandler::sendResponse(const String &text) {
    Serial.println(text);
}
