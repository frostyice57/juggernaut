#pragma once
#include <Adafruit_PWMServoDriver.h>
#include <Arduino.h>

#include "SerialHandler.h"

#define SERVOMIN 110   // This is the 'minimum' pulse length count (out of 4096)
#define SERVOMAX 505   // This is the 'maximum' pulse length count (out of 4096)
#define USMIN 600      // This is the rounded 'minimum' microsecond length based on the minimum pulse of 150
#define USMAX 2400     // This is the rounded 'maximum' microsecond length based on the maximum pulse of 600
#define SERVO_FREQ 50  // Analog servos run at ~50 Hz updates
#define ANGLMIN 0
#define ANGLMAX 180
#define FIRSTSERVO 0  // The first servo channel

// Simple OOP wrapper around Adafruit_PWMServoDriver for managing multiple servos
// For ESP8266 we avoid dynamic heap fragmentation by using fixed-size arrays.
#ifndef PWMSC_MAX_SERVOS
#define PWMSC_MAX_SERVOS 16
#endif

class PWMServoController {
   public:
    PWMServoController(uint8_t numServos = 8, uint8_t i2cAddr = 0x40);
    void begin();

    // Call frequently from main loop to advance non-blocking motions
    void update();

    // Low-level control
    bool setAngle(uint8_t servoIndex, uint8_t angle);
    bool setAllAngles(uint8_t angles[]);
    // Non-blocking moves
    bool moveServoTo(uint8_t servoIndex, uint8_t angle, unsigned long durationMs = 0, uint8_t easing = 0);
    void moveAllServosTo(const uint8_t angles[], unsigned long durationMs = 0, uint8_t easing = 0);

    // Optionally handle text commands passed from SerialHandler
    void handleCommand(const String &cmd, SerialHandler *serial = nullptr);

   private:
    enum EasingType { EASE_LINEAR = 0,
                      EASE_IN_OUT_CUBIC = 1,
                      EASE_IN_QUAD = 2,
                      EASE_OUT_QUAD = 3,
                      EASE_IN_OUT_SINE = 4 };

    struct Motion {
        float startDeg;
        float targetDeg;
        unsigned long startTime;
        unsigned long duration;
        bool moving;
        uint8_t easing;
    };

    uint8_t _numServos;
    Adafruit_PWMServoDriver _pwm;
    float _pwmPerDegree;
    // current angles (float for interpolation) - fixed storage
    float _angles[PWMSC_MAX_SERVOS];
    // motions per servo - fixed storage
    Motion _motions[PWMSC_MAX_SERVOS];
    // default motion parameters
    uint8_t _speed;          // 0..10 where 10 is fastest (shorter duration)
    uint8_t _defaultEasing;  // one of EasingType

    int pulseFromAngle(float angle);
    // easing functions
    static float easeLinear(float t);
    static float easeInOutCubic(float t);
    static float easeInQuad(float t);
    static float easeOutQuad(float t);
    static float easeInOutSine(float t);
};
