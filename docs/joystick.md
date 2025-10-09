# Game Controller Setup Guide for Raspberry Pi

This guide explains how to pair and test an **Xbox or PlayStation controller** wirelessly via Bluetooth on a Raspberry Pi.
It assumes you are using **Raspberry Pi OS Bookworm** or **Bullseye**.

---

## Prerequisites

Ensure your system is up to date. On most Bookworm installations, Bluetooth support is already included. The only extra package needed is `joystick` to use the testing tool.

```bash
sudo apt update
sudo apt upgrade -y
sudo apt install -y joystick
```

Verify that Bluetooth is active:

```bash
systemctl status bluetooth
```

If you see `active (running)`, you are ready.

---

## Supported Controllers

| Controller                  | Works via Bluetooth | Notes                                                                                  |
| --------------------------- | ------------------- | -------------------------------------------------------------------------------------- |
| Xbox One S / Series X       | Yes                 | Requires Bluetooth 4.0+; may need `xpadneo` driver for full rumble and battery support |
| PlayStation DualShock 4     | Yes                 | Fully supported by built-in Linux driver `hid-sony`                                    |
| PlayStation DualSense (PS5) | Yes                 | Supported by `hid-playstation` driver in kernel 5.12+                                  |

---

## Pairing the Controller

### 1. Start Bluetooth services

```bash
sudo systemctl enable bluetooth
sudo systemctl start bluetooth
```

### 2. Enter the Bluetooth shell

```bash
bluetoothctl
```

Then run:

```text
power on
agent on
default-agent
scan on
```

---

### 3. Put the controller in pairing mode

* **Xbox controller:** Hold the **Pair** button (on top near the USB port) until the Xbox logo blinks rapidly.
* **PlayStation controller:** Hold **Share + PS** buttons together until the light bar flashes quickly.

---

### 4. Wait for detection

When the controller is found, you will see output like:

```
[NEW] Device DC:0C:2D:AB:1E:5A Xbox Wireless Controller
```

or

```
[NEW] Device 04:5D:4B:8A:BB:9E Wireless Controller
```

---

### 5. Pair and connect

Replace <MAC> with the detected Bluetooth address:

```text
pair <MAC>
trust <MAC>
connect <MAC>
```

Once connected, the controller light becomes solid.

---

### 6. Verify input device

Exit `bluetoothctl` and check:

```bash
ls /dev/input/
```

You should see something like:

```
js0
```

Test it:

```bash
jstest /dev/input/js0
```

Move the sticks or press buttons to confirm input is detected.

---

## Troubleshooting

### Controller not detected

Restart Bluetooth services:

```bash
sudo systemctl restart bluetooth
```

If still not listed, unpair and try again:

```bash
bluetoothctl
remove <MAC>
```

### Controller disconnects automatically

Controllers enter sleep mode when idle. Press the main button (Xbox logo or PS button) to reconnect.
