import time
import numpy as np

try:
    from vl53l5cx_ctypes import VL53L5CX  # type: ignore[import]
except ModuleNotFoundError as exc:
    raise ModuleNotFoundError(
        "Missing dependency 'vl53l5cx_ctypes' in the active Python environment. "
        "Install it with: pip install vl53l5cx-ctypes"
    ) from exc

# -------- INIT --------
sensor = VL53L5CX()
sensor.init()
sensor.start_ranging()

THRESHOLD = 3000  # mm
MIN_VALID = 50
MAX_VALID = 4000

print("Jetson ToF Object Detection Started\n")

# -------- SMOOTH FILTER --------
last_dist = 0

def smooth(val):
    global last_dist
    if last_dist == 0:
        last_dist = val
    else:
        last_dist = 0.7 * last_dist + 0.3 * val
    return last_dist

# -------- LOOP --------
while True:

    if sensor.data_ready():

        data = sensor.get_data()
        grid = np.array(data).reshape(8, 8)

        valid_values = []

        left = grid[:, :3]
        center = grid[:, 3:5]
        right = grid[:, 5:]

        for val in grid.flatten():
            if MIN_VALID < val < MAX_VALID:
                valid_values.append(val)

        if not valid_values:
            print("No valid object")
            print("----------------------")
            time.sleep(0.1)
            continue

        min_dist = min(valid_values)
        min_dist = smooth(min_dist)

        # -------- DIRECTION --------
        direction = "UNKNOWN"

        if np.min(center) < THRESHOLD:
            direction = "CENTER"
        elif np.min(left) < THRESHOLD:
            direction = "LEFT"
        elif np.min(right) < THRESHOLD:
            direction = "RIGHT"

        # -------- OUTPUT --------
        if min_dist < THRESHOLD:

            dist_cm = min_dist / 10.0

            print("OBJECT DETECTED")
            print(f"Distance: {dist_cm:.1f} cm")
            print(f"Direction: {direction}")

        else:
            print("No object nearby")

        print("----------------------")

    time.sleep(0.1)