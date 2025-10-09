import Jetson.GPIO as GPIO
import time
import subprocess
import threading
import socket
import os

# GPIO Pin Configuration
GPIO.setwarnings(False)
GPIO.setmode(GPIO.BOARD)
relay_pin = 32
GPIO.setup(relay_pin, GPIO.OUT)

# TCP Configuration
HOST, PORT = "113.54.252.151", 5001

# Function to run the camera.sh script and send images afterward
def run_camera_script_and_send_images():
    try:
        subprocess.run(["bash", "/home/nvidia/camera.sh"])  # Run the camera script
        print("Camera script completed. Starting to send images...")
        send_images()  # Send images after the script finishes
    except KeyboardInterrupt:
        print("Camera script interrupted.")
        return

# Function to handle GPIO relay logic
def control_relay():
    try:
        while True:
            GPIO.output(relay_pin, GPIO.LOW)  # Example logic: turn relay off
    except KeyboardInterrupt:
        GPIO.output(relay_pin, GPIO.HIGH)  # Ensure relay is off when interrupted
        print("Relay control interrupted.")
        return

# Function to send images via TCP
def send_images():
    try:
        image_folder = 'images'
        image_files = sorted(
    [os.path.join(image_folder, f) for f in os.listdir(image_folder) if os.path.isfile(os.path.join(image_folder, f))],
    key=lambda x: os.path.getmtime(x)  # 按文件修改时间排序
)

        for image_path in image_files:
            try:
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.connect((HOST, PORT))
                # print(f"Connected to server {HOST}:{PORT}")

                arrBuf = bytearray(b'\xff\xaa\xff\xaa')

                with open(image_path, 'rb') as picData:
                    picBytes = picData.read()

                picSize = len(picBytes)
                datalen = 64 + picSize

                arrBuf += bytearray(datalen.to_bytes(4, byteorder='little'))
                guid = 23458283482894382928948
                arrBuf += bytearray(guid.to_bytes(64, byteorder='little'))
                arrBuf += picBytes

                sock.sendall(arrBuf)
                print(f"Sent image: {image_path}")
            except Exception as e:
                print(f"Error sending image {image_path}: {e}")
            finally:
                sock.close()
    except KeyboardInterrupt:
        print("Image sending interrupted.")
        return

# Create threads for parallel execution
relay_thread = threading.Thread(target=control_relay)
camera_thread = threading.Thread(target=run_camera_script_and_send_images)

# Set threads as daemon so they terminate when the main program exits
relay_thread.daemon = True
camera_thread.daemon = True

# Start threads
relay_thread.start()
camera_thread.start()

# Main program to handle KeyboardInterrupt and clean up
try:
    # Wait for threads to complete
    camera_thread.join()
    relay_thread.join()

except KeyboardInterrupt:
    print("Program interrupted by user.")

finally:
    # Ensure GPIO is cleaned up even if interrupted
    GPIO.cleanup()
    print("Program Exited.")
