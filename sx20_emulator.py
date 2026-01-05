import serial
import time
import subprocess
import logging

# --- Configuration ---
SERIAL_PORT = '/dev/ttyS0'
BAUD_RATE = 115200
LOG_FILE = '/home/pi/sx20_debug.log'

# Setup Logging
logging.basicConfig(
    filename=LOG_FILE,
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

def set_pi_volume(change):
    try:
        logging.info(f"Adjusting volume: {change}")
        subprocess.run(['amixer', 'sset', 'Master', change], stdout=subprocess.DEVNULL)
    except Exception as e:
        logging.error(f"Failed to set volume: {e}")

def toggle_mute():
    try:
        logging.info("Toggling mute state")
        subprocess.run(['amixer', 'sset', 'Master', 'toggle'], stdout=subprocess.DEVNULL)
    except Exception as e:
        logging.error(f"Failed to toggle mute: {e}")

def minimize_all_windows():
    try:
        logging.info("Minimizing all windows")
        subprocess.run(['wmctrl', '-k', 'on'], stdout=subprocess.DEVNULL)
    except Exception as e:
        logging.error(f"Failed to minimize all windows: {e}")

def move_mouse(x, y):
    try:
        logging.info(f"Moving mouse {x} {y}")
        subprocess.run(['xdotool', 'mousemove_relative', '--', str(x), str(y)], stdout=subprocess.DEVNULL)
    except Exception as e:
        logging.error(f"Failed to move mouse {x} {y}: {e}")

def click_mouse(code=1):
    try:
        logging.info(f"Clicking mouse {code}")
        subprocess.run(['xdotool', 'click', str(code)], stdout=subprocess.DEVNULL)
    except Exception as e:
        logging.error(f"Failed to click mouse {code}: {e}")

def run_emulator():
    logging.info("Starting SX20 Emulator...")
    try:
        ser = serial.Serial(
            port=SERIAL_PORT,
            baudrate=BAUD_RATE,
            parity=serial.PARITY_NONE,
            stopbits=serial.STOPBITS_ONE,
            bytesize=serial.EIGHTBITS,
            timeout=1
        )
        logging.info(f"Serial port {SERIAL_PORT} opened successfully.")
    except Exception as e:
        logging.critical(f"Could not open serial port: {e}")
        return

    # Emulate Boot
    boot_sequence = [
        "U-Boot 2010.06-40 (May 04 2015 - 12:04:13)",
        "DRAM:  2 GiB",
        "Starting kernel ...",
        "Welcome to 192.168.0.19",
        "Cisco Codec Release TC7.3.4.e4daf54",
        "*r Login successful",
        "\nOK\n"
    ]

    for line in boot_sequence:
        ser.write((line + "\r\n").encode())
        time.sleep(0.1)

    while True:
        if ser.in_waiting > 0:
            try:
                # Read and log raw input for debugging
                raw_data = ser.readline()
                line = raw_data.decode('utf-8', errors='ignore').strip()

                if not line:
                    continue

                logging.debug(f"Received: {repr(line)}") # repr shows hidden chars like \r

                response = "Command not recognized.\r\n"

                if "xStat camera 1 Connected" in line:
                    response = "*s Camera 1 Connected: False\r\n** end\r\nOK\r\n"

                elif "VolumeUp" in line:
                    set_pi_volume('5%+')
                    response = "*r KeyClickResult (status=OK):\r\n** end\r\nOK\r\n"

                elif "VolumeDown" in line:
                    set_pi_volume('5%-')
                    response = "*r KeyClickResult (status=OK):\r\n** end\r\nOK\r\n"

                elif "MuteMic" in line:
                    toggle_mute()
                    response = "*r KeyClickResult (status=OK):\r\n** end\r\nOK\r\n"
                elif "xCommand Key Click Key:Home" in line:
                    minimize_all_windows()
                    response = "*r KeyClickResult (status=OK):\r\n** end\r\nOK\r\n"

                elif "xCommand Key Click Key:Up" in line:
                    move_mouse(0, -10)
                    response = "*r KeyClickResult (status=OK):\r\n** end\r\nOK\r\n"

                elif "xCommand Key Click Key:Down" in line:
                    move_mouse(0, 10)
                    response = "*r KeyClickResult (status=OK):\r\n** end\r\nOK\r\n"

                elif "xCommand Key Click Key:Left" in line:
                    move_mouse(-10, 0)
                    response = "*r KeyClickResult (status=OK):\r\n** end\r\nOK\r\n"

                elif "xCommand Key Click Key:Right" in line:
                    move_mouse(10, 0)
                    response = "*r KeyClickResult (status=OK):\r\n** end\r\nOK\r\n"

                elif "xCommand Key Click Key:Ok" in line:
                    click_mouse(1)
                    response = "*r KeyClickResult (status=OK):\r\n** end\r\nOK\r\n"

                elif "xCommand Key Click Key:" in line:
                    response = "*r KeyClickResult (status=OK):\r\n** end\r\nOK\r\n"

                logging.debug(f"Sent: {repr(response)}")
                ser.write(response.encode())

            except Exception as e:
                logging.error(f"Loop error: {e}")

if __name__ == "__main__":
    run_emulator()

