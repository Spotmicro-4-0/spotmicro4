# Raspberry Pi CPU Profiling Guide

## Overview
This guide explains how to monitor CPU usage of a Python-based robotics program on a Raspberry Pi using three simultaneous SSH sessions:
1. **Session 1:** Runs the robot code.
2. **Session 2:** Monitors live CPU usage with `htop`.
3. **Session 3:** Profiles Python function-level CPU hotspots with `py-spy`.

---

## 1. SSH Sessions Setup
Open **three separate SSH connections** to your Raspberry Pi, for example:
```bash
ssh pi@spotmicroai.local
ssh pi@spotmicroai.local
ssh pi@spotmicroai.local
```
Each will be used for a different tool.

---

## 2. Session 1 – Run Your Code
Activate your virtual environment and start your main Python script:
```bash
cd ~/spotmicroai
source venv/bin/activate
./runtime.sh
```
Confirm it’s running in the background and note its PID:
```bash
pgrep -f spotmicroai/main.py
```

---

## 3. Session 2 – Monitor System Load (htop)
Start **htop** to monitor system-wide CPU, memory, and process usage:
```bash
htop
```
Key controls inside `htop`:
- `F6` → Sort by CPU%
- `F5` → Toggle Tree view (off for global sort)
- `H`  → Toggle Threads view
- `q`  → Quit

Watch for your process (e.g. `venv/bin/python3 spotmicroai/main.py`) and note the CPU%.

---

## 4. Session 3 – Profile Python Code (py-spy)
Install `py-spy` if not already:
```bash
source ~/spotmicroai/venv/bin/activate
pip install py-spy
```
Run it against the process ID from Session 1:
```bash
sudo /home/pi/spotmicroai/venv/bin/py-spy top --pid <PID>
```
Observe the top functions consuming CPU.

To record a flamegraph for 10 seconds:
```bash
sudo /home/pi/spotmicroai/venv/bin/py-spy record -o profile.svg --pid <PID> --duration 10
```
Then copy the file back to your desktop and open it:
```bash
scp pi@spotmicroai.local:~/spotmicroai/profile.svg .
```

---

## 5. Interpreting Results
| Tool | What to Look For | Typical Action |
|------|------------------|----------------|
| **htop** | High CPU from `main.py` even when idle | Indicates busy loop |
| **py-spy** | Top function names (e.g., `do_process_events_from_queues`, `move`) | Add small `time.sleep()` or blocking queue read |

---

## 6. Recommended Loop Adjustment
If your idle loop runs constantly, throttle it:
```python
while True:
    event = queue.get(timeout=0.01)  # blocks briefly
    handle_event(event)
```
This prevents 100% CPU when the robot is inactive.

---

## Summary
| Session | Purpose | Key Command |
|----------|----------|--------------|
| 1 | Run your code | `./runtime.sh` |
| 2 | Watch system load | `htop` |
| 3 | Profile code | `sudo py-spy top --pid <PID>` |

Once you’ve identified the busy function, optimize it and repeat to confirm CPU drops when idle.
