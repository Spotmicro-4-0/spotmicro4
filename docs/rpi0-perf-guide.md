# Raspberry Pi Performance & Throttling Debugging Guide

This guide provides a comprehensive procedure for investigating and debugging performance, throttling, and responsiveness issues on Raspberry Pi devices. It is designed for developers maintaining field-deployed systems or diagnosing slow behavior.

---

## 1. Overview
When your Raspberry Pi feels sluggish, freezes for several seconds, or behaves unpredictably, the cause usually falls into one of these categories:
- **CPU bottlenecks** (processes overloading cores)
- **Memory exhaustion or swap thrashing**
- **SD card I/O latency or filesystem corruption**
- **Power supply or thermal throttling**

The following sections outline step-by-step methods to identify and fix these issues.

---

## 2. Checking CPU Utilization

### Commands
```bash
top
# or, for better visualization
htop
```

### Interpretation
- **High %CPU on one process**: That process dominates a single core.
- **wa (I/O wait)**: Indicates the CPU is waiting for slow disk or network I/O.
- **load average**: Roughly, the number of runnable or waiting processes. A load higher than the number of cores (>4 on a Pi Zero 2 W) suggests overload.

### Recommendations
- Identify high-usage processes and inspect their logs or code.
- Use `nice` or `systemd` service limits to reduce CPU priority.
- For Python services, check for tight loops or unbounded polling.

---

## 3. Checking Memory Usage

### Commands
```bash
free -h
```

### Interpretation
| Column | Meaning |
|---------|----------|
| **used** | Total RAM consumed by programs |
| **available** | RAM still available without swapping |
| **Swap used** | Nonzero means memory pressure |

If swap usage > 0 and available < 50 MB, you are thrashing the SD card.

### Recommendations
- Increase swap file size:
  ```bash
  sudo nano /etc/dphys-swapfile
  CONF_SWAPSIZE=512
  sudo dphys-swapfile setup && sudo systemctl restart dphys-swapfile
  ```
- Optimize Python or Node.js processes to release unused memory.

---

## 4. Checking Temperature and Power Throttling

### Commands
```bash
vcgencmd measure_temp
vcgencmd get_throttled
```

### Interpretation
- **Temperature output:** Normal < 65°C, throttling risk > 80°C.
- **Throttled flag:**
  - `throttled=0x0` means normal operation.
  - Non-zero indicates under-voltage or thermal throttling.

### Recommendations
- Ensure a **5V 2.5A+** power supply and quality cable.
- Add a heatsink or small fan if under sustained load.

---

## 5. Checking SD Card Performance and Health

### Commands
Install utilities:
```bash
sudo apt install sysstat
```
Then run:
```bash
iostat -xz 1 3
```

### Interpretation
| Metric | Meaning | Healthy Range |
|---------|----------|----------------|
| **r_await / w_await** | Average read/write latency | < 5 ms |
| **%util** | Disk utilization | < 90% sustained |
| **wareq-sz** | Write request size | Consistent values (~32–512 KB) |

If `w_await > 50 ms` or high I/O wait (`%iowait` > 10%), the SD card is slowing the system.

### Test raw write speed
```bash
dd if=/dev/zero of=/tmp/test bs=4M count=20 conv=fdatasync
```
Expected result: **> 10 MB/s** for a healthy card.

### Check filesystem and kernel logs
```bash
sudo dmesg | egrep -i "mmc|error|fail|timeout|ext4"
```
If you see messages like `orphan cleanup` or `read-only fs`, the filesystem is recovering from corruption.

### Recommendations
- Replace slow or damaged SD cards.
- Mount filesystems with `noatime` to reduce writes:
  ```bash
  PARTUUID=<id>  /  ext4  defaults,noatime  0  1
  ```
- Move logs to RAM to reduce wear:
  ```bash
  tmpfs /tmp tmpfs defaults,noatime,nosuid,size=64m 0 0
  tmpfs /var/log tmpfs defaults,noatime,nosuid,size=64m 0 0
  ```

---

## 6. Investigating Boot and Journal Logs

### Commands
```bash
sudo journalctl -b -1 -p 0..3
sudo journalctl -p err -S -2h
```

### Interpretation
- `-b -1`: Shows previous boot (useful after a crash).
- `-p 0..3`: Shows only errors and critical issues.
- Look for repeated service restarts or kernel panics.

If the Pi silently rebooted, check:
```bash
last -x | head
```

---

## 7. Checking for I/O or DNS Blocking

### Tests
```bash
time ls /
time hostname -f
```
If `hostname -f` stalls, add this line to `/etc/hosts`:
```
127.0.1.1   raspberrypi
```
This avoids slow reverse DNS lookups that can freeze `sudo` and other commands.

---

## 8. Recommended High-Performance SD Cards

| Brand / Model | Type | Performance Tier | Notes |
|----------------|-------|------------------|--------|
| **SanDisk Extreme microSDXC UHS-I** | A2 / U3 / V30 | ★★★★★ | Excellent random I/O; balanced speed and endurance |
| **Samsung PRO Plus microSDXC** | A2 / U3 / V30 | ★★★★★ | Great sustained writes and reliability |
| **Kingston High Endurance** | A1 / U3 | ★★★★☆ | Designed for heavy write cycles |
| **PNY PRO Elite High Endurance** | A2 / V30 | ★★★★☆ | Good value endurance card |
| **ProGrade Digital UHS-II microSDXC** | UHS-II / V60 | ★★★★☆ | Backward compatible; very high speed |
| **VIOFO Industrial Grade microSD** | U3 / A2 / V30 | ★★★★★ | Industrial spec; great for robotics and harsh environments |

### Buying Tips
- Prefer **A1 or A2** rated cards (optimized for random access).
- Avoid no-name or fake cards (common on marketplaces).
- Use **64–256 GB** capacity for best performance/wear balance.
- Always benchmark new cards using `dd` or `fio` after flashing.

---

## 9. General Optimization Tips
- Disable HDMI if unused:
  ```bash
  sudo /usr/bin/tvservice -o
  ```
- Minimize logging or move logs to a remote syslog.
- Avoid unnecessary background services:
  ```bash
  systemctl list-unit-files --type=service | grep enabled
  sudo systemctl disable <service>
  ```

---

## 10. Quick Diagnostic Summary
| Subsystem | Key Command | Healthy Range / Result |
|------------|--------------|------------------------|
| CPU | `top` / `htop` | < 80% sustained usage |
| Memory | `free -h` | > 50 MB available, no swap use |
| Power | `vcgencmd get_throttled` | `throttled=0x0` |
| SD I/O | `iostat -xz 1 3` | `w_await < 5ms`, `%util < 90%` |
| Write speed | `dd` test | > 10 MB/s |
| Errors | `dmesg | egrep -i "mmc|error|fail"` | none |

---

### Author’s Note
This guide was derived from real-world diagnostics on Raspberry Pi Zero 2 W systems used in robotics deployments. The commands and interpretations apply to all Raspberry Pi models running Debian Bookworm or