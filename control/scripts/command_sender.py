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
        speed = 9
        while True:
            line = lines[idx]
            print(f"TX -> {line}")

            if line.startswith("W"):
                # leaves only numbers in the substring, good for additional comments in commands
                wait_ms = int(''.join(ch for ch in line[1:].strip() if ch.isdigit()) ) * (1 + (2 / 10 * (10 - speed)))
                tik = time.perf_counter()
                print(f"Waiting {wait_ms} ms")
                time.sleep(wait_ms / 1000)
                tok = time.perf_counter()
                print(f"Actual wait time: {(tok - tik) * 1000:.2f} ms")
            else:
                # Ensure a terminating newline so receiver sees a full line
                data = (line + "\n").encode("utf-8")
                ser.write(data)


            if line.startswith("V"):
                speed = int(line[1:].strip())

            idx += 1
            if idx >= len(lines):
                if loop:
                    idx = loop_idx
                else:
                    break

            if line.strip() == "----------":
                loop_idx = idx
            time.sleep(interval)
    finally:
        ser.close()


def main():
    p = argparse.ArgumentParser(description="Send lines from a file periodically over serial.")
    p.add_argument("--file", default="commands.txt", help="Path to text file with one command per line.")
    p.add_argument("--port", default="COM3", help="Serial port (e.g. COM3 or /dev/ttyACM0).")
    p.add_argument("--baud", type=int, default=115200, help="Baud rate (default 115200).")
    p.add_argument("--interval", type=float, default=0.008, help="Seconds between lines (default 0.2).")
    # good alt intervals: 0.004, 0.006, 0.008
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
