#!/usr/bin/env python3
import sys
import time
import argparse
from collections import deque

try:
    import serial
    import serial.tools.list_ports
except ImportError:
    print("Error: 'pyserial' package is not installed. Run 'pip install pyserial'")
    sys.exit(1)

# Default configuration
DEFAULT_PORT = "COM5"
DEFAULT_BAUD = 9600
MAX_POINTS = 200  # Number of points to display in rolling plot

def parse_telemetry(line):
    """
    Parses a telemetry line like: Raw_Knob:234,Smoothed_Knob:235,Target_Power_%:22
    Returns a dictionary of key-value pairs or None if invalid.
    """
    try:
        parts = line.strip().split(',')
        data = {}
        for part in parts:
            if ':' in part:
                key, val = part.split(':', 1)
                data[key.strip()] = float(val.strip())
        return data
    except Exception:
        return None

def run_console_monitor(port, baud):
    """Fallback text-based monitor if GUI is not requested or available."""
    print(f"Connecting to {port} at {baud} baud (Console Mode)...")
    try:
        ser = serial.Serial(port, baud, timeout=1.0)
        # Clear buffers
        ser.reset_input_buffer()
        print("Connected! Press Ctrl+C to stop.")
        print("-" * 60)
        print(f"{'Time':<12} | {'Raw Knob':<10} | {'Smoothed':<10} | {'Power %':<10}")
        print("-" * 60)
        
        while True:
            if ser.in_waiting:
                line = ser.readline().decode('utf-8', errors='ignore')
                data = parse_telemetry(line)
                if data:
                    raw = data.get("Raw_Knob", 0.0)
                    smoothed = data.get("Smoothed_Knob", 0.0)
                    power = data.get("Target_Power_%", 0.0)
                    timestamp = time.strftime("%H:%M:%S")
                    print(f"{timestamp:<12} | {raw:<10.0f} | {smoothed:<10.1f} | {power:<10.0f}%", end='\r')
            time.sleep(0.01)
            
    except serial.SerialException as e:
        print(f"\nSerial connection error: {e}")
    except KeyboardInterrupt:
        print("\nMonitoring stopped by user.")

def run_gui_plotter(port, baud):
    """Graphical plotter using Matplotlib."""
    try:
        import matplotlib.pyplot as plt
        import matplotlib.animation as animation
    except ImportError:
        print("Matplotlib not installed. Falling back to Console Monitor.")
        run_console_monitor(port, baud)
        return

    print(f"Connecting to {port} at {baud} baud (GUI Plotter Mode)...")
    try:
        ser = serial.Serial(port, baud, timeout=1.0)
        ser.reset_input_buffer()
    except serial.SerialException as e:
        print(f"Failed to open port {port}: {e}")
        print("Available COM ports:")
        for p in serial.tools.list_ports.comports():
            print(f" - {p.device}: {p.description}")
        return

    # Deques to store rolling data
    times = deque(maxlen=MAX_POINTS)
    raw_vals = deque(maxlen=MAX_POINTS)
    smooth_vals = deque(maxlen=MAX_POINTS)
    power_vals = deque(maxlen=MAX_POINTS)
    
    start_time = time.time()

    # Set up matplotlib style and figures
    plt.style.use('dark_background')
    fig, (ax1, ax2) = plt.subplots(2, 1, sharex=True, figsize=(10, 6))
    fig.canvas.manager.set_window_title(f"Espresso Controller Telemetry - {port}")

    # Subplot 1: Knob readings
    line_raw, = ax1.plot([], [], label='Raw Knob', color='#ff6b6b', alpha=0.5, linewidth=1.5)
    line_smooth, = ax1.plot([], [], label='Smoothed Knob (EMA)', color='#4dabf7', linewidth=2)
    ax1.set_ylabel('Knob Input (0-1023)')
    ax1.set_ylim(-50, 1074)
    ax1.grid(True, color='#444444', linestyle='--')
    ax1.legend(loc='upper left')
    ax1.set_title('Potentiometer Filter Analysis', fontsize=12, pad=10, color='#e9ecef')

    # Subplot 2: Output Power
    line_power, = ax2.plot([], [], label='Target Power %', color='#51cf66', linewidth=2)
    ax2.set_xlabel('Elapsed Time (s)')
    ax2.set_ylabel('TRIAC Power Output (%)')
    ax2.set_ylim(-5, 105)
    ax2.grid(True, color='#444444', linestyle='--')
    ax2.legend(loc='upper left')

    # Status/Telemetry text on figure
    status_text = fig.text(0.5, 0.01, 'Waiting for telemetry data...', 
                           ha='center', va='bottom', color='#f1f3f5', fontsize=10)

    def init():
        line_raw.set_data([], [])
        line_smooth.set_data([], [])
        line_power.set_data([], [])
        return line_raw, line_smooth, line_power

    def update(frame):
        # Read all pending lines to stay in real-time
        data_packet = None
        while ser.in_waiting:
            try:
                line = ser.readline().decode('utf-8', errors='ignore')
                parsed = parse_telemetry(line)
                if parsed:
                    data_packet = parsed
            except Exception:
                pass
        
        if data_packet:
            elapsed = time.time() - start_time
            times.append(elapsed)
            raw_vals.append(data_packet.get("Raw_Knob", 0.0))
            smooth_vals.append(data_packet.get("Smoothed_Knob", 0.0))
            power_vals.append(data_packet.get("Target_Power_%", 0.0))
            
            # Update plot lines
            t_list = list(times)
            line_raw.set_data(t_list, list(raw_vals))
            line_smooth.set_data(t_list, list(smooth_vals))
            line_power.set_data(t_list, list(power_vals))
            
            # Rescale X axis dynamically
            if t_list:
                ax2.set_xlim(max(0, t_list[-1] - 15), t_list[-1] + 1)
            
            # Update status text
            status_text.set_text(
                f"Port: {port} | Raw: {raw_vals[-1]:.0f} | "
                f"Smoothed: {smooth_vals[-1]:.1f} | Power: {power_vals[-1]:.0f}%"
            )
            
        return line_raw, line_smooth, line_power

    # Run the animation
    ani = animation.FuncAnimation(fig, update, init_func=init, interval=30, blit=False, cache_frame_data=False)
    
    plt.tight_layout()
    plt.subplots_adjust(bottom=0.08)
    
    try:
        plt.show()
    except KeyboardInterrupt:
        pass
    finally:
        ser.close()
        print("Port closed. Plotter exit.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Arduino Espresso Controller Serial Plotter")
    parser.add_argument("-p", "--port", default=DEFAULT_PORT, help=f"Serial port (default: {DEFAULT_PORT})")
    parser.add_argument("-b", "--baud", type=int, default=DEFAULT_BAUD, help=f"Baud rate (default: {DEFAULT_BAUD})")
    parser.add_argument("-c", "--console", action="store_true", help="Run in text console mode instead of GUI plotter")
    
    args = parser.parse_args()
    
    if args.console:
        run_console_monitor(args.port, args.baud)
    else:
        run_gui_plotter(args.port, args.baud)
