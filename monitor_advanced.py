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
        from matplotlib.widgets import CheckButtons
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
    flow_vals = deque(maxlen=MAX_POINTS)
    pressure_vals = deque(maxlen=MAX_POINTS)
    
    start_time = time.time()

    # Set up matplotlib style and figures
    plt.style.use('dark_background')
    fig, (ax1, ax2, ax3) = plt.subplots(3, 1, sharex=True, figsize=(10, 8))
    fig.canvas.manager.set_window_title(f"Espresso Controller Telemetry - {port}")
    plt.subplots_adjust(left=0.25, bottom=0.08)

    # Subplot 1: Knob readings
    line_raw, = ax1.plot([], [], label='Raw Knob', color='#ff6b6b', alpha=0.5, linewidth=1.5)
    line_smooth, = ax1.plot([], [], label='Smoothed Knob (EMA)', color='#4dabf7', linewidth=2)
    ax1.set_ylabel('Knob Input (0-1023)')
    ax1.set_ylim(-50, 1074)
    ax1.grid(True, color='#444444', linestyle='--')
    ax1.legend(loc='upper right')
    ax1.set_title('Potentiometer Filter Analysis', fontsize=12, pad=10, color='#e9ecef')

    # Add CheckButtons
    rax = plt.axes([0.02, 0.75, 0.15, 0.15], facecolor='#2b2b2b')
    check = CheckButtons(
        ax=rax,
        labels=('Raw Knob', 'Smoothed Knob'),
        actives=(True, True),
        label_props={'color': ['#ff6b6b', '#4dabf7']}
    )
    
    def toggle_lines(label):
        if label == 'Raw Knob':
            line_raw.set_visible(not line_raw.get_visible())
        elif label == 'Smoothed Knob':
            line_smooth.set_visible(not line_smooth.get_visible())
        fig.canvas.draw_idle()
    
    check.on_clicked(toggle_lines)

    # Subplot 2: Output Power
    line_power, = ax2.plot([], [], label='Target Power %', color='#51cf66', linewidth=2)
    ax2.set_ylabel('TRIAC Power Output (%)')
    ax2.set_ylim(-5, 105)
    ax2.grid(True, color='#444444', linestyle='--')
    ax2.legend(loc='upper left')

    # Subplot 3: Estimated Flow & Pressure
    ax3.set_xlabel('Elapsed Time (s)')
    ax3.set_ylabel('Flow Rate (ml/min)', color='#fcc419')
    line_flow, = ax3.plot([], [], label='Estimated Flow', color='#fcc419', linewidth=2)
    ax3.tick_params(axis='y', labelcolor='#fcc419')
    ax3.set_ylim(0, 700)
    ax3.grid(True, color='#444444', linestyle='--')
    
    ax3_twin = ax3.twinx()
    ax3_twin.set_ylabel('Pressure (bar)', color='#cc5de8')
    line_pressure, = ax3_twin.plot([], [], label='Estimated Pressure', color='#cc5de8', linewidth=2)
    ax3_twin.tick_params(axis='y', labelcolor='#cc5de8')
    ax3_twin.set_ylim(0, 20)

    # Combine legends for ax3 and ax3_twin
    lines = [line_flow, line_pressure]
    labels = [l.get_label() for l in lines]
    ax3.legend(lines, labels, loc='upper left')

    # Status/Telemetry text on figure
    status_text = fig.text(0.5, 0.01, 'Waiting for telemetry data...', 
                           ha='center', va='bottom', color='#f1f3f5', fontsize=10)

    def init():
        line_raw.set_data([], [])
        line_smooth.set_data([], [])
        line_power.set_data([], [])
        line_flow.set_data([], [])
        line_pressure.set_data([], [])
        return line_raw, line_smooth, line_power, line_flow, line_pressure

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
            
            power = data_packet.get("Target_Power_%", 0.0)
            power_vals.append(power)
            
            # ULKA EX5 Calculations:
            # 100% duty cycle ~ 650 ml/min and 15 bar (max static)
            flow = power * (650.0 / 100.0)
            pressure = power * (15.0 / 100.0)
            
            flow_vals.append(flow)
            pressure_vals.append(pressure)
            
            # Update plot lines
            t_list = list(times)
            line_raw.set_data(t_list, list(raw_vals))
            line_smooth.set_data(t_list, list(smooth_vals))
            line_power.set_data(t_list, list(power_vals))
            line_flow.set_data(t_list, list(flow_vals))
            line_pressure.set_data(t_list, list(pressure_vals))
            
            # Rescale X axis dynamically
            if t_list:
                ax3.set_xlim(max(0, t_list[-1] - 15), t_list[-1] + 1)
            
            # Update status text
            status_text.set_text(
                f"Port: {port} | Power: {power_vals[-1]:.0f}% | "
                f"Flow: {flow_vals[-1]:.1f} ml/min | Pres: {pressure_vals[-1]:.1f} bar"
            )
            
        return line_raw, line_smooth, line_power, line_flow, line_pressure

    # Run the animation
    ani = animation.FuncAnimation(fig, update, init_func=init, interval=30, blit=False, cache_frame_data=False)
    
    # We already adjusted the subplot layout earlier, removing this tight_layout which might reset it.
    # plt.tight_layout()
    # plt.subplots_adjust(bottom=0.08)
    
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
