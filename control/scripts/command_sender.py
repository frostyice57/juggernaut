import argparse
import time
import sys
import serial

#!/usr/bin/env python3
"""
command_sender.py

Periodically sends one line from a selected text file over a serial port.

Defaults inspired by typical servo_controller.py settings:
- baudrate: 115200
- 8N1, timeout 1s
"""

def send_lines(port, baud, filepath, interval, loop):
    ser = serial.Serial(
        port=port,
        baudrate=baud,
        bytesize=serial.EIGHTBITS,
        parity=serial.PARITY_NONE,
        stopbits=serial.STOPBITS_ONE,
        timeout=1,
    )
    try:
        with open(filepath, "r", encoding="utf-8", errors="replace") as f:
            lines = [ln.rstrip("\r\n") for ln in f]
        if not lines:
            print("File is empty.", file=sys.stderr)
            return
        idx = 0
        loop_idx = 0
        while not loop_idx:
            line = lines[idx]
            # Ensure a terminating newline so receiver sees a full line
            data = (line + "\n").encode("utf-8")
            ser.write(data)
            # Optional: wait for any echoed response (non-blocking due to timeout)
            # resp = ser.readline()
            # if resp:
            #     print("RX:", resp.decode(errors="replace").rstrip())
            print(f"TX -> {line}")
            idx += 1
            if idx >= len(lines):
                break
            if line.strip() == "----------":
                print("Starting main loop...")
                loop_idx = idx
                break
            time.sleep(interval)
        while True:
            line = lines[idx]
            # Ensure a terminating newline so receiver sees a full line
            data = (line + "\n").encode("utf-8")
            ser.write(data)
            # Optional: wait for any echoed response (non-blocking due to timeout)
            # resp = ser.readline()
            # if resp:
            #     print("RX:", resp.decode(errors="replace").rstrip())
            print(f"TX -> {line}")
            idx += 1
            if idx >= len(lines):
                if loop:
                    idx = loop_idx
                else:
                    break
            time.sleep(interval)
    finally:
        ser.close()

def main():
    p = argparse.ArgumentParser(description="Send lines from a file periodically over serial.")
    p.add_argument("--file", default="commands.txt", help="Path to text file with one command per line.")
    p.add_argument("--port", default="COM3", help="Serial port (e.g. COM3 or /dev/ttyACM0).")
    p.add_argument("--baud", type=int, default=115200, help="Baud rate (default 115200).")
    p.add_argument("--interval", type=float, default=0.01, help="Seconds between lines (default 0.2).")
    p.add_argument("--loop", default="True", action="store_true", help="Loop file indefinitely.")
    args = p.parse_args()

    try:
        send_lines(args.port, args.baud, args.file, args.interval, args.loop)
    except KeyboardInterrupt:
        print("\nStopped by user.", file=sys.stderr)
    except Exception as e:
        print("Error:", e, file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()