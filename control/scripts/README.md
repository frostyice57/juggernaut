# Servo Controller

This project consists of an Arduino program and a Python GUI application for controlling up to 8 servos using a PCA9685 PWM servo driver board.

## Arduino Code

The Arduino code (`src/main.cpp`) has been modified to:
- Accept serial commands in the format `S<servo_num>:<degrees>`
- Control 8 servos (channels 0-7)
- Accept degrees from 0-180 and automatically convert to PWM values (150-600)
- Provide feedback via serial monitor including both degrees and PWM values
- Initialize all servos to center position (90 degrees) on startup

### Command Format
- `S0:90` - Sets servo 0 to 90 degrees (center position)
- `S7:180` - Sets servo 7 to 180 degrees (maximum position)
- `S3:0` - Sets servo 3 to 0 degrees (minimum position)
- Degree range: 0-180 (automatically converted to PWM range 150-600)

## Python GUI Application

The Python application (`servo_controller/servo_controller.py`) provides:
- Sliders for each of the 8 servos (0-180 degrees)
- Real-time position feedback in degrees
- Serial port selection and connection management
- Individual servo centering (90 degrees)
- Emergency stop functionality
- Center all servos button (90 degrees)

### Installation

1. Install Python dependencies:
   ```
   pip install -r servo_controller/requirements.txt
   ```

2. Run the application:
   ```
   python servo_controller/servo_controller.py
   ```

### Usage

1. Upload the Arduino code to your microcontroller
2. Connect your PCA9685 board and servos
3. Run the Python application
4. Select the correct COM port from the dropdown
5. Click "Connect"
6. Use the sliders to control individual servos
7. The position values will be sent to the Arduino in real-time

### Hardware Setup

- Connect PCA9685 to your microcontroller via I2C (SDA/SCL)
- Connect servos to channels 0-7 on the PCA9685
- Ensure proper power supply for the servos (typically 5V or 6V)
- The PCA9685 VCC should be connected to 3.3V or 5V depending on your board

### Features

- **Real-time Control**: Move sliders to instantly control servo positions
- **Position Feedback**: See exact position values for each servo
- **Center Controls**: Individual or all-servo centering
- **Emergency Stop**: Quickly center all servos
- **Connection Management**: Easy connect/disconnect with status indication
- **Error Handling**: Validates commands and handles communication errors

### Troubleshooting

- Ensure the correct COM port is selected
- Check that the Arduino is properly connected and programmed
- Verify I2C connections between microcontroller and PCA9685
- Make sure servos are properly powered
- Check serial monitor for Arduino feedback and error messages
