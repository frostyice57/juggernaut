#include <Arduino.h>
#include "SerialHandler.h"
#include "PWMServoController.h"

// Global objects
SerialHandler serialHandler;
PWMServoController servoController(8, 0x40);

void setup() {
    Serial.begin(115200);
    serialHandler.begin();
    servoController.begin();

    Serial.println("Servo controller (OOP) ready");
}

void loop() {
    // Poll serial handler to accumulate lines
    serialHandler.poll();

    // If a command is ready, let servoController handle it
    if (serialHandler.hasCommand()) {
        String cmd = serialHandler.getCommand();
        servoController.handleCommand(cmd, &serialHandler);
    }

    // Progress non-blocking servo motions
    servoController.update();

    // Minimal main loop: no blocking calls here
}