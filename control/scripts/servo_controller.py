import tkinter as tk
from tkinter import ttk, messagebox
from tkinter.scrolledtext import ScrolledText
import serial
import serial.tools.list_ports
import threading
import time


class ServoController:
    def __init__(self, master):
        self.master = master
        self.master.title("8-Channel Servo Controller")
        self.master.geometry("560x820")

        # Serial connection
        self.serial_connection = None
        self.is_connected = False
        # Background reader thread control
        self.read_thread = None
        self.read_thread_stop = threading.Event()
        # Resend thread control (re-send last command until acknowledged)
        self.resend_thread = None
        self.resend_thread_stop = threading.Event()
        # Last sent command tracking
        self.last_command = None  # dict: {'cmd': str, 'retries': int}
        self.last_command_lock = threading.Lock()

        # Servo parameters
        self.num_servos = 8
        self.servo_turn_min = 60  # 0 degrees
        self.servo_turn_max = 120  # 120 degrees
        self.servo_lift_min = 55  # 0 degrees
        self.servo_lift_max = 125  # 120 degrees
        self.servo_positions = [90] * self.num_servos  # Center position (90 degrees)

        # GUI elements
        self.sliders = []
        self.position_labels = []
        # Console widgets
        self.console = None
        self.console_entry = None

        self.setup_gui()
        self.connect_serial()

    def setup_gui(self):
        # Main frame
        main_frame = ttk.Frame(self.master, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))

        # Connection frame
        conn_frame = ttk.LabelFrame(main_frame, text="Serial Connection", padding="5")
        conn_frame.grid(row=0, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 10))

        # COM port selection
        ttk.Label(conn_frame, text="COM Port:").grid(row=0, column=0, padx=(0, 5))
        self.port_var = tk.StringVar()
        self.port_combo = ttk.Combobox(conn_frame, textvariable=self.port_var, state="readonly")
        self.port_combo.grid(row=0, column=1, padx=(0, 10))

        # Refresh ports button
        ttk.Button(conn_frame, text="Refresh", command=self.refresh_ports).grid(row=0, column=2, padx=(0, 10))

        # Connect/Disconnect button
        self.connect_button = ttk.Button(conn_frame, text="Connect", command=self.toggle_connection)
        self.connect_button.grid(row=0, column=3)

        # Status label
        self.status_label = ttk.Label(conn_frame, text="Disconnected", foreground="red")
        self.status_label.grid(row=0, column=4, padx=(10, 0))

        # Servo control frame
        servo_frame = ttk.LabelFrame(main_frame, text="Servo Controls", padding="5")
        servo_frame.grid(row=1, column=0, columnspan=2, sticky=(tk.W, tk.E, tk.N, tk.S), pady=(0, 10))

        # Create sliders for each servo
        for i in range(self.num_servos):
            # Servo label
            ttk.Label(servo_frame, text=f"Servo {i}:").grid(row=i, column=0, padx=(0, 10), pady=2, sticky=tk.W)

            # Position slider (now in degrees)
            slider = tk.Scale(
                servo_frame,
                from_=self.servo_turn_min if i < 4 else self.servo_lift_min,
                to=self.servo_turn_max if i < 4 else self.servo_lift_max,
                orient=tk.HORIZONTAL,
                length=300,
                command=lambda val, servo_num=i: self.slider_changed(servo_num, val),
            )
            slider.set(self.servo_positions[i])
            slider.grid(row=i, column=1, padx=(0, 10), pady=2)
            self.sliders.append(slider)

            # Position value label (now shows degrees)
            pos_label = ttk.Label(servo_frame, text=f"{self.servo_positions[i]}°")
            pos_label.grid(row=i, column=2, padx=(0, 10), pady=2)
            self.position_labels.append(pos_label)

            # Reset button for individual servo
            ttk.Button(servo_frame, text="Center", command=lambda servo_num=i: self.center_servo(servo_num)).grid(
                row=i, column=3, pady=2
            )

        # Control buttons frame
        button_frame = ttk.Frame(main_frame)
        button_frame.grid(row=2, column=0, columnspan=2, pady=(0, 10))

        # Center all servos button
        ttk.Button(button_frame, text="Center All Servos", command=self.center_all_servos).grid(
            row=0, column=0, padx=(0, 10)
        )

        # Emergency stop button
        ttk.Button(button_frame, text="Emergency Stop", command=self.emergency_stop, style="Emergency.TButton").grid(
            row=0, column=1
        )

        # Configure emergency button style
        style = ttk.Style()
        style.configure("Emergency.TButton", foreground="red")

        # Configure grid weights
        self.master.columnconfigure(0, weight=1)
        self.master.rowconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=1)
        main_frame.rowconfigure(1, weight=1)

        # Initialize port list
        self.refresh_ports()

        # Console frame (incoming messages + raw send)
        console_frame = ttk.LabelFrame(main_frame, text="Console", padding="5")
        console_frame.grid(row=3, column=0, columnspan=2, sticky=(tk.W, tk.E, tk.N, tk.S))

        self.console = ScrolledText(console_frame, height=12, state="disabled", wrap="none")
        self.console.grid(row=0, column=0, columnspan=3, sticky=(tk.W, tk.E))

        self.console_entry = ttk.Entry(console_frame)
        self.console_entry.grid(row=1, column=0, sticky=(tk.W, tk.E), pady=(5, 0))
        # Send on Enter key
        self.console_entry.bind("<Return>", lambda e: self.send_raw_from_entry())
        ttk.Button(console_frame, text="Send", command=self.send_raw_from_entry).grid(
            row=1, column=1, padx=(5, 0), pady=(5, 0)
        )
        ttk.Button(console_frame, text="Clear", command=self.clear_console).grid(
            row=1, column=2, padx=(5, 0), pady=(5, 0)
        )

        console_frame.columnconfigure(0, weight=1)

    def refresh_ports(self):
        """Refresh the list of available COM ports"""
        ports = serial.tools.list_ports.comports()
        port_names = [port.device for port in ports]

        self.port_combo["values"] = port_names
        if port_names and not self.port_var.get():
            self.port_combo.current(0)

    def toggle_connection(self):
        """Connect or disconnect from the serial port"""
        if not self.is_connected:
            self.connect_serial()
        else:
            self.disconnect_serial()

    def connect_serial(self):
        """Connect to the selected serial port"""
        port = self.port_var.get()
        if not port:
            messagebox.showerror("Error", "Please select a COM port")
            return

        try:
            self.serial_connection = serial.Serial(port, 115200, timeout=0.1)
            time.sleep(2)  # Wait for Arduino to reset

            self.is_connected = True
            self.connect_button.config(text="Disconnect")
            self.status_label.config(text="Connected", foreground="green")

            # Send initial positions to all servos
            for i in range(self.num_servos):
                self.send_servo_command(i, self.servo_positions[i])

            # Start background read thread
            self.read_thread_stop.clear()
            self.read_thread = threading.Thread(target=self.serial_read_loop, daemon=True)
            self.read_thread.start()
            # Start resend thread
            self.resend_thread_stop.clear()
            self.resend_thread = threading.Thread(target=self._resend_loop, daemon=True)
            self.resend_thread.start()

        except serial.SerialException as e:
            messagebox.showerror("Connection Error", f"Failed to connect to {port}: {str(e)}")

    def disconnect_serial(self):
        """Disconnect from the serial port"""
        # Stop reader thread
        if self.read_thread:
            self.read_thread_stop.set()
            self.read_thread.join(timeout=0.5)
            self.read_thread = None
        # Stop resend thread
        if self.resend_thread:
            self.resend_thread_stop.set()
            self.resend_thread.join(timeout=0.5)
            self.resend_thread = None

        if self.serial_connection:
            self.serial_connection.close()
            self.serial_connection = None

        self.is_connected = False
        self.connect_button.config(text="Connect")
        self.status_label.config(text="Disconnected", foreground="red")

    def send_servo_command(self, servo_num, degrees):
        """Send servo position command to Arduino (in degrees)"""
        if self.is_connected and self.serial_connection:
            try:
                command = f"S{servo_num}:{degrees}\n"
                self.serial_connection.write(command.encode())
                self.serial_connection.flush()
            except serial.SerialException as e:
                messagebox.showerror("Communication Error", f"Failed to send command: {str(e)}")
                self.disconnect_serial()

    def append_to_console(self, text):
        """Append a message to the console text widget"""
        if self.console:
            self.console.configure(state="normal")
            self.console.insert(tk.END, text + "\n")
            self.console.see(tk.END)  # Scroll to end
            self.console.configure(state="disabled")

    def clear_console(self):
        """Clear the console text widget"""
        if self.console:
            self.console.configure(state="normal")
            self.console.delete("1.0", tk.END)
            self.console.configure(state="disabled")

    def send_raw_from_entry(self):
        """Send raw command from entry field to serial port"""
        raw_command = self.console_entry.get().strip()
        if raw_command and self.is_connected:
            try:
                cmd = f"{raw_command}\n"
                self.serial_connection.write(cmd.encode())
                self.serial_connection.flush()
                # Track last command for potential resend
                with self.last_command_lock:
                    self.last_command = {"cmd": cmd.strip(), "retries": 0}
                self.console_entry.delete(0, tk.END)  # Clear entry field
            except serial.SerialException as e:
                messagebox.showerror("Communication Error", f"Failed to send command: {str(e)}")
                self.disconnect_serial()

    def serial_read_loop(self):
        """Background thread reading incoming serial data and appending to console"""
        while not self.read_thread_stop.is_set():
            try:
                if self.serial_connection and self.serial_connection.in_waiting:
                    data = self.serial_connection.read(self.serial_connection.in_waiting)
                    if data:
                        # Safely decode bytes to string, replacing invalid sequences
                        s = data.decode("utf-8", errors="replace")
                        # handle possibly multiple lines
                        lines = s.splitlines()
                        for line in lines:
                            trimmed = line.rstrip("\r\n")
                            # Schedule GUI update and handler on main thread
                            self.master.after(0, self.append_to_console, trimmed)
                            self.master.after(0, self._handle_incoming_line, trimmed)
                # small sleep to avoid busy loop
                time.sleep(0.01)
            except serial.SerialException:
                # Stop on serial exception
                self.master.after(0, self.append_to_console, "Serial error - disconnected")
                self.master.after(0, self.disconnect_serial)
                return

    def _handle_incoming_line(self, line):
        """Run on GUI/main thread: inspect incoming line and ACK or mark for resend."""
        txt = line.strip()
        if not txt:
            return

        # If device reports invalid command or input overflow, schedule immediate resend
        if "Invalid" in txt or "overflow" in txt or "Invalid command format" in txt:
            # On error, ensure resend thread will attempt again
            # Optionally append note
            with self.last_command_lock:
                if self.last_command:
                    # bump retries so resend loop can act
                    self.last_command["retries"] = max(0, self.last_command.get("retries", 0))
            return
        # Commands not containing "Invalid" are accepted, consider acknowledged
        else:
            # clear last command
            with self.last_command_lock:
                self.last_command = None
            return

    def _resend_loop(self):
        """Background loop that resends last_command until acknowledged."""
        base_interval = 0.2
        max_interval = 5.0
        while not self.resend_thread_stop.is_set():
            with self.last_command_lock:
                cmd_info = None if not self.last_command else dict(self.last_command)
            if cmd_info and self.is_connected and self.serial_connection:
                try:
                    # Prepare local values to avoid race conditions
                    cmd_str = cmd_info.get("cmd")
                    retries = cmd_info.get("retries", 0)
                    if cmd_str is None:
                        interval = 1.0
                    else:
                        # Send the command
                        self.serial_connection.write((cmd_str + "\n").encode())
                        self.serial_connection.flush()
                        # increment retry count in shared state
                        with self.last_command_lock:
                            if self.last_command and self.last_command.get("cmd") == cmd_str:
                                self.last_command["retries"] = self.last_command.get("retries", 0) + 1
                        # compute backoff
                        interval = min(max_interval, base_interval * (2**retries))
                except serial.SerialException:
                    # will be handled by read thread or connect logic
                    interval = 1.0
                # wait before next attempt, checking stop flag frequently
                waited = 0.0
                while waited < interval and not self.resend_thread_stop.is_set():
                    time.sleep(0.05)
                    waited += 0.05
                continue
            # No pending command, sleep briefly
            time.sleep(0.1)

    def slider_changed(self, servo_num, value):
        """Handle slider value changes"""
        degrees = int(value)
        self.servo_positions[servo_num] = degrees
        self.position_labels[servo_num].config(text=f"{degrees}°")

        # Send command to Arduino
        self.send_servo_command(servo_num, degrees)

    def center_servo(self, servo_num):
        """Center a specific servo (90 degrees)"""
        center_degrees = 90
        self.sliders[servo_num].set(center_degrees)
        self.servo_positions[servo_num] = center_degrees
        self.position_labels[servo_num].config(text=f"{center_degrees}°")
        self.send_servo_command(servo_num, center_degrees)

    def center_all_servos(self):
        """Center all servos (90 degrees)"""
        center_degrees = 90
        for i in range(self.num_servos):
            self.sliders[i].set(center_degrees)
            self.servo_positions[i] = center_degrees
            self.position_labels[i].config(text=f"{center_degrees}°")
            self.send_servo_command(i, center_degrees)

    def emergency_stop(self):
        """Emergency stop - center all servos immediately"""
        if messagebox.askyesno("Emergency Stop", "Center all servos immediately?"):
            self.center_all_servos()

    def on_closing(self):
        """Handle application closing"""
        if self.is_connected:
            self.disconnect_serial()
        self.master.destroy()


def main():
    root = tk.Tk()
    app = ServoController(root)

    # Handle window closing
    root.protocol("WM_DELETE_WINDOW", app.on_closing)

    root.mainloop()


if __name__ == "__main__":
    main()
