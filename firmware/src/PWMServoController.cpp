#include "PWMServoController.h"

PWMServoController::PWMServoController(uint8_t numServos, uint8_t i2cAddr)
    : _numServos(numServos), _pwm(i2cAddr) {
    // clamp to maximum to avoid overflow of static arrays
    if (_numServos > PWMSC_MAX_SERVOS) _numServos = PWMSC_MAX_SERVOS;
    for (uint8_t i = 0; i < _numServos; ++i) {
        _angles[i] = 90.0f;  // center
        _motions[i].startDeg = _angles[i];
        _motions[i].targetDeg = _angles[i];
        _motions[i].startTime = 0;
        _motions[i].duration = 0;
        _motions[i].moving = false;
        _motions[i].easing = EASE_LINEAR;
    }
    // defaults
    _speed = 5;
    _defaultEasing = EASE_LINEAR;
}

void PWMServoController::begin() {
    _pwm.begin();
    _pwm.setOscillatorFrequency(27000000);
    _pwm.setPWMFreq(50);
    // compute mapping from degrees to PWM counts
    _pwmPerDegree = float(SERVOMAX - SERVOMIN) / float(ANGLMAX - ANGLMIN);

    // initialize outputs to center
    for (uint8_t i = 0; i < _numServos; ++i) {
        int pulse = pulseFromAngle(_angles[i]);
        _pwm.setPWM(i, 0, pulse);
    }
}

int PWMServoController::pulseFromAngle(float angle) {
    return SERVOMIN + int(angle * _pwmPerDegree + 0.5f);
}

bool PWMServoController::setAngle(uint8_t servoIndex, uint8_t angle) {
    if (servoIndex >= _numServos || angle < ANGLMIN || angle > ANGLMAX) return false;
    _angles[servoIndex] = (float)angle;
    int pulse = pulseFromAngle(_angles[servoIndex]);
    _pwm.setPWM(servoIndex, 0, pulse);
    // cancel any running motion
    _motions[servoIndex].moving = false;
    return true;
}

bool PWMServoController::setAllAngles(uint8_t angles[]) {
    for (uint8_t servoIndex = 0; servoIndex < _numServos; ++servoIndex) {
        if (angles[servoIndex] < ANGLMIN || angles[servoIndex] > ANGLMAX) return false;
        _angles[servoIndex] = (float)angles[servoIndex];
        int pulse = pulseFromAngle(_angles[servoIndex]);
        _pwm.setPWM(servoIndex, 0, pulse);
        // cancel any running motion
        _motions[servoIndex].moving = false;
    }
    return true;
}

bool PWMServoController::moveServoTo(uint8_t servoIndex, uint8_t angle, unsigned long durationMs, uint8_t easing) {
    if (servoIndex >= _numServos) return false;
    if (angle < ANGLMIN) angle = ANGLMIN;
    if (angle > ANGLMAX) angle = ANGLMAX;
    if (durationMs == 0) return setAngle(servoIndex, angle);

    _motions[servoIndex].startDeg = _angles[servoIndex];
    _motions[servoIndex].targetDeg = angle;
    _motions[servoIndex].startTime = millis();
    _motions[servoIndex].duration = durationMs;
    _motions[servoIndex].moving = true;
    _motions[servoIndex].easing = easing;
    return true;
}

void PWMServoController::moveAllServosTo(const uint8_t angles[], unsigned long durationMs, uint8_t easing) {
    for (uint8_t i = 0; i < _numServos; ++i) {
        moveServoTo(i, angles[i], durationMs, easing);
    }
}

void PWMServoController::handleCommand(const String &cmd, SerialHandler *serial) {
    // Very small command language similar to previous sketch
    // S<servo>:<deg>  - set single servo immediately
    // M ... reserved for future multi-servo moves
    if (cmd.length() == 0) return;
    // Single servo move: S<idx>:<deg>
    if (cmd.startsWith("S") && cmd.indexOf(':') > 0) {
        int colon = cmd.indexOf(':');
        int semi = cmd.indexOf(';');
        int idx = cmd.substring(1, colon).toInt();
        int deg = cmd.substring(colon + 1, semi < 0 ? cmd.length() : semi).toInt();
        unsigned long duration = 0;
        // compute duration from speed
        if (idx >= 0 && idx < _numServos) {
            float start = _angles[idx];
            int angular = abs(deg - (int)start);
            if (semi < 0) {
                duration = (unsigned long)(angular * (10 - _speed));
                if (serial) serial->sendResponse(String("Duration") + String(duration)); //!Delete
            } else {
                duration = cmd.substring(semi + 1).toInt() * (1.0 + (2.0 * (10.0 - _speed)) / 10.0);  // scale by speed
                if (serial) serial->sendResponse(String("Duration") + String(duration)); //!Delete
            }
            if (moveServoTo((uint8_t)idx, (uint8_t)deg, duration, _defaultEasing)) {
                if (serial) serial->sendResponse(cmd);
            } else {
                if (serial) serial->sendResponse("Invalid");
            }
        } else {
            if (serial) serial->sendResponse("InvalidIndex");
        }
    }
    // Set speed: V<0-10>
    else if (cmd.startsWith("V")) {
        int v = cmd.substring(1).toInt();
        if (v < 0) v = 0;
        if (v > 10) v = 10;
        _speed = (uint8_t)v;
        if (serial) serial->sendResponse(String("V") + String(_speed));
    }
    // Set default easing: E<id>
    else if (cmd.startsWith("E")) {
        int e = cmd.substring(1).toInt();
        if (e < 0) e = EASE_LINEAR;
        if (e > (int)EASE_IN_OUT_SINE) e = EASE_LINEAR;
        _defaultEasing = (uint8_t)e;
        if (serial) serial->sendResponse(String("E") + String(_defaultEasing));
    }
    // Multi-servo move: M:<a0>,<a1>,...,<aN>
    else if (cmd.startsWith("M") && cmd.indexOf(':') > 0) {
        int colon = cmd.indexOf(':');
        String body = cmd.substring(colon + 1);
        // parse comma-separated angles
        uint8_t targets[PWMSC_MAX_SERVOS];
        for (uint8_t i = 0; i < _numServos; ++i) targets[i] = (uint8_t)roundf(_angles[i]);

        unsigned int idx = 0;
        unsigned int start = 0;
        while (start < body.length() && idx < _numServos) {
            int comma = body.indexOf(',', start);
            String tok;
            if (comma < 0) {
                tok = body.substring(start);
                start = body.length();
            } else {
                tok = body.substring(start, comma);
                start = comma + 1;
            }
            tok.trim();
            if (tok.length() > 0) {
                int deg = tok.toInt();
                if (deg < ANGLMIN) deg = ANGLMIN;
                if (deg > ANGLMAX) deg = ANGLMAX;
                targets[idx++] = (uint8_t)deg;
            }
        }

        // compute max angular distance
        int maxDiff = 0;
        for (uint8_t i = 0; i < _numServos; ++i) {
            int diff = abs((int)targets[i] - (int)roundf(_angles[i]));
            if (diff > maxDiff) maxDiff = diff;
        }
        unsigned long duration = (unsigned long)(maxDiff * (10 - _speed));
        moveAllServosTo(targets, duration, _defaultEasing);
        if (serial) serial->sendResponse(cmd);
    } else if (cmd.startsWith("L")) {
        // List angles
        if (serial) {
            for (uint8_t i = 0; i < _numServos; ++i) {
                serial->sendResponse("S" + String(i) + ":" + String(_angles[i]));
            }
        }
        // List speed
        if (serial) {
            serial->sendResponse("V" + String(_speed));
        }
        // List default easing
        if (serial) {
            serial->sendResponse("E" + String(_defaultEasing));
        }
    } else if (cmd.startsWith("H")) {
        // Help command
        if (serial) {
            serial->sendResponse("Commands:");
            serial->sendResponse(" S<servo>:<deg>  - Set servo position");
            serial->sendResponse(" M:<a0>,<a1>,...,<aN> - Move multiple servos");
            serial->sendResponse(" V<speed>      - Set speed (0-10)");
            serial->sendResponse(" E<easing>    - Set default easing");
            serial->sendResponse(" L             - List all servo angles");
        }
    } else {
        if (serial) serial->sendResponse("UnknownCmd");
    }
}

// Easing implementations
float PWMServoController::easeLinear(float t) { return t; }
float PWMServoController::easeInOutCubic(float t) {
    if (t < 0.5f) return 4.0f * t * t * t;
    float f = (2.0f * t) - 2.0f;
    return 0.5f * f * f * f + 1.0f;
}
float PWMServoController::easeInQuad(float t) { return t * t; }
float PWMServoController::easeOutQuad(float t) { return t * (2 - t); }
float PWMServoController::easeInOutSine(float t) { return -0.5f * (cosf(M_PI * t) - 1.0f); }

void PWMServoController::update() {
    unsigned long now = millis();
    for (uint8_t i = 0; i < _numServos; ++i) {
        if (!_motions[i].moving) continue;
        unsigned long elapsed = now - _motions[i].startTime;
        float t = _motions[i].duration == 0 ? 1.0f : (float)elapsed / (float)_motions[i].duration;
        if (t >= 1.0f) {
            _angles[i] = _motions[i].targetDeg;
            _motions[i].moving = false;
        } else if (t <= 0.0f) {
            _angles[i] = _motions[i].startDeg;
        } else {
            float eased;
            switch (_motions[i].easing) {
                case EASE_IN_OUT_CUBIC:
                    eased = easeInOutCubic(t);
                    break;
                case EASE_IN_QUAD:
                    eased = easeInQuad(t);
                    break;
                case EASE_OUT_QUAD:
                    eased = easeOutQuad(t);
                    break;
                case EASE_IN_OUT_SINE:
                    eased = easeInOutSine(t);
                    break;
                case EASE_LINEAR:
                default:
                    eased = easeLinear(t);
                    break;
            }
            _angles[i] = _motions[i].startDeg + (_motions[i].targetDeg - _motions[i].startDeg) * eased;
        }

        int pulse = pulseFromAngle(_angles[i]);
        _pwm.setPWM(i, 0, pulse);
    }
}
