# ESP32-S3 Sense HTTP/MJPEG camera

The sketch is for the XIAO ESP32S3 Sense with its OV2640 camera. It serves a
single JPEG at `/capture`, an MJPEG stream at `/stream`, and status JSON at
`/health`.

## Build

```sh
arduino-cli compile \
  --fqbn esp32:esp32:esp32s3 \
  firmware/esp32-sense-mjpeg
```

The default SSID is the requested iPhone hotspot, `iPhoneA13`. No Wi-Fi
password is stored in this repository; inject it only at compile/upload time
with `SYODO_WIFI_PASSWORD`. If the password is left empty, the board tries the
SSID briefly and then starts an isolated access point named `syodo-cam-XXXX`
(the last four hex digits come from the board MAC), password `syodo-cam`; use
`http://192.168.4.1/` after joining that network.

For a password that contains shell-special characters, pass it through an
environment variable in the current shell rather than putting it in source or
the command history:

```sh
read -s WIFI_PASSWORD
arduino-cli compile \
  --fqbn esp32:esp32:esp32s3 \
  --build-property "build.extra_flags=-DSYODO_WIFI_SSID=\"iPhoneA13\" -DSYODO_WIFI_PASSWORD=\"$WIFI_PASSWORD\"" \
  firmware/esp32-sense-mjpeg
unset WIFI_PASSWORD
```

## Compile and upload (explicit action)

`arduino-cli upload` does not compile first. Use one temporary build directory
so the password-bearing binary is not left in the repository:

```sh
BUILD_DIR="$(mktemp -d -t syodo-esp32-mjpeg)"
read -s WIFI_PASSWORD
arduino-cli compile \
  --fqbn esp32:esp32:esp32s3 \
  --build-path "$BUILD_DIR" \
  --build-property "build.extra_flags=-DSYODO_WIFI_SSID=\"iPhoneA13\" -DSYODO_WIFI_PASSWORD=\"$WIFI_PASSWORD\"" \
  firmware/esp32-sense-mjpeg
arduino-cli upload \
  --input-dir "$BUILD_DIR" \
  --port /dev/cu.usbmodem2101 \
  --fqbn esp32:esp32:esp32s3
unset WIFI_PASSWORD
```

The port must be the ESP32 camera (`/dev/cu.usbmodem2101` in the current
setup), not the SO-101 Leader port. Keep the board connected and confirm the
AP/Wi-Fi choice before uploading.

## Mac-side capture

On `iPhoneA13`, use the `HTTP camera: http://<address>/` address printed in
the ESP32 serial log. The AP fallback uses the fixed address below:

```sh
.venv/bin/python scripts/esp32_camera.py health http://192.168.4.1
.venv/bin/python scripts/esp32_camera.py capture http://192.168.4.1
.venv/bin/python scripts/esp32_camera.py stream http://192.168.4.1 --seconds 10
```

Files are saved below `runs/esp32-camera/<timestamp>/` unless an output path is
provided. The camera is configured for VGA JPEG frames and a modest stream
rate to avoid the frame-buffer overflow reported by the previous firmware.
