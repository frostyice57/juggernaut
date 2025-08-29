# Quadruped Walking Robot

This project contains the design, firmware, control software, and documentation for a quadruped walking robot. The robot is powered by a microcontroller controlling servos, with high-level commands sent from a host computer.


## Project Structure

- **firmware/** – Embedded C++ code for the microcontroller
  - **src/** – Main firmware source code
  - **lib/** – Third-party or custom libraries
  - **tests/** – Unit tests for firmware (optional)

- **control/** – Host-side control (Python, C++, ROS, etc.)
  - **scripts/** – Python scripts for serial communication and gait control
  - **modules/** – Reusable Python modules/classes
  - **notebooks/** – Jupyter notebooks for testing and debugging (optional)

- **simulation/** – Physics or kinematics simulation
  - **gazebo/** – Gazebo world and robot description files
  - **pybullet/** – PyBullet or Isaac Gym simulation models
  - **matlab/** – MATLAB/Simulink models or analysis

- **cad/** – Mechanical design
  - **fusion/** – Fusion 360 source files ^(.f3d^)
  - **stl/** – Exported STL files for 3D printing
  - **step/** – STEP files for manufacturing/sharing
  - **renders/** – Images and renders for documentation

- **docs/** – Documentation
  - **design/** – Design notes, block diagrams
  - **hardware/** – Wiring diagrams, schematics
  - **usage/** – Setup instructions and tutorials

- **tests/** – Integration and system tests
  - **logs/** – Test run outputs, performance logs

- **utils/** – Helper scripts (build, deployment, calibration)


## Getting Started

1. Clone the repository.
2. Open `firmware/` for embedded MCU code or `control/` for host-side scripts.
3. See `docs/` for setup and usage instructions.

## License

MIT License (see LICENSE file)
