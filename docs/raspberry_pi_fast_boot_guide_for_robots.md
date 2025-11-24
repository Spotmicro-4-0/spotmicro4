# Fast-Boot Linux Guide for Raspberry Pi Robots (Wi‑Fi + Bluetooth)

This guide shows you how to turn a Raspberry Pi–based robot into a **fast-booting, headless machine** while keeping **Wi‑Fi and Bluetooth** working.

You’ll learn how to:

- Measure boot time and find the biggest time-wasting services
- Switch from graphical to text-mode boot
- Disable or remove heavyweight services (Snap, cloud-init, ModemManager, etc.)
- Tweak Pi boot settings
- Add your robot app as a systemd service
- Measure progress after each change

The examples assume **Ubuntu on Raspberry Pi**, but almost everything applies to other systemd-based distros (including Raspberry Pi OS) with minor path/name changes.

---

## 1. Prerequisites & Safety

### 1.1. What you need

- A Raspberry Pi (4/5 or similar) running a systemd-based Linux (Ubuntu Server or Raspberry Pi OS Lite recommended)
- Shell access (keyboard + monitor, or SSH)
- A backup or SD card image you can restore if something goes wrong

### 1.2. Safety principles

Before you start disabling services, keep these rules in mind:

- **Change one thing at a time.** After each change, reboot and re-measure.
- **Never disable core systemd components** like `systemd-udevd`, `dbus`, `systemd-logind`, `systemd-journald`.
- **Don’t disable your network or SSH** unless you’re absolutely sure you won’t need remote access.
- Keep notes so you can undo changes (or turn them into a reproducible setup script later).

---

## 2. Measure Boot Time (Baseline)

First, get your baseline boot performance. Reboot the Pi, log in, then run:

```bash
systemd-analyze
```

Sample output:

```text
Startup finished in 6.325s (kernel) + 13.858s (userspace) = 20.183s
```

- **Kernel**: Time from power-on to when the Linux kernel hands control to userspace
- **Userspace**: Time from PID 1 (systemd) startup to reaching the default target (multi-user or graphical)

### 2.1. Find long-running services

List services ordered by how long they took to start:

```bash
systemd-analyze blame
```

You’ll get lines like:

```text
5.992s snapd.seeded.service
5.786s snapd.service
5.047s networkd-dispatcher.service
3.659s cloud-init-main.service
3.145s ssh.service
...
```

The top items are your **prime candidates** for optimization or removal.

### 2.2. See the critical boot chain

Not every long-running service actually delays reaching the target. To see what blocks the boot path:

```bash
systemd-analyze critical-chain
```

This shows which services are on the critical path from boot to the default target.

You’ll refer back to these commands **after each round of changes** to confirm that boot time is improving.

---

## 3. Switch to Text-Mode Boot (No GUI)

Robots almost never need a full desktop environment. Booting to a text console shaves off time and memory usage.

### 3.1. Set the default target to multi-user

```bash
sudo systemctl set-default multi-user.target
```

Reboot:

```bash
sudo reboot
```

After reboot, check:

```bash
systemd-analyze
systemd-analyze critical-chain
```

You should see something like:

```text
multi-user.target reached after Xs in userspace
```

instead of `graphical.target`. This alone can make a noticeable difference on desktop-leaning images.

If you ever need the GUI back:

```bash
sudo systemctl set-default graphical.target
sudo reboot
```

---

## 4. Eliminate Heavy Services (Snap, cloud-init, ModemManager, etc.)

This section targets services that commonly appear near the top of `systemd-analyze blame` but are not needed for a headless robot.

> **Important:** Always confirm with `systemd-analyze blame` which services are actually slow on your system before disabling them.

### 4.1. Snap (snapd & snapd.seeded)

On Ubuntu, **Snap** is a major contributor to userspace boot time.

You’ll often see things like:

```text
5.992s snapd.seeded.service
5.786s snapd.service
```

If your robot **does not rely on snap packages**, you can disable Snap completely.

#### 4.1.1. Disable Snap services

```bash
sudo systemctl disable --now snapd.service snapd.seeded.service
```

Reboot and recheck:

```bash
sudo reboot
# then after login
systemd-analyze
systemd-analyze blame | head -20
```

You should no longer see `snapd` entries, and userspace boot time should drop significantly.

#### 4.1.2. (Optional) Remove snapd

Once you’re sure nothing uses Snap:

```bash
sudo apt purge snapd
```

This will free disk space and prevent Snap from coming back in future updates.

---

### 4.2. Cloud-Init

On many cloud images, **cloud-init** configures the system at first boot. On a Pi robot, it’s usually dead weight after initial setup and can add several seconds to boot.

You might see services like:

- `cloud-init.service`
- `cloud-init-local.service`
- `cloud-config.service`
- `cloud-final.service`

Often one of them shows prominently in `systemd-analyze blame`, e.g.:

```text
3.659s cloud-init-main.service
```

#### 4.2.1. Disable cloud-init

```bash
sudo systemctl disable --now \
  cloud-init.service \
  cloud-init-local.service \
  cloud-config.service \
  cloud-final.service
```

Reboot and re-measure.

#### 4.2.2. (Optional) Remove cloud-init

When you’re confident the system no longer depends on it:

```bash
sudo apt purge cloud-init
```

---

### 4.3. ModemManager (3G/4G modems)

If your robot only uses **Wi‑Fi and Bluetooth** (no cellular modem), you can safely remove **ModemManager**.

You might see:

```text
1.371s ModemManager.service
```

Disable it:

```bash
sudo systemctl disable --now ModemManager.service
```

Reboot and check that Wi‑Fi/Bluetooth still work. ModemManager is only for mobile broadband devices.

---

### 4.4. Optional: Other “Nice-to-Have” Services

These services can also add a bit of time. You can disable them **if you understand the trade-offs** and don’t rely on their functionality.

#### 4.4.1. Apport (crash reporter)

Ubuntu’s crash reporting service:

```bash
sudo systemctl disable --now apport.service
```

You’ll lose automatic crash popups/uploading, but your robot doesn’t need popups.

#### 4.4.2. Pollinate (entropy seeding)

Pollinate contacts Ubuntu’s infrastructure to help seed randomness:

```bash
sudo systemctl disable --now pollinate.service
```

For an offline robot, this is usually unnecessary.

#### 4.4.3. e2scrub (filesystem scrubber)

This helps monitor and scrub ext4 filesystems. If your robot is on a reasonably reliable SD card and you shut down cleanly, you can disable it for faster boots:

```bash
sudo systemctl disable --now e2scrub_reap.service
sudo systemctl disable --now e2scrub_all.timer 2>/dev/null || true
```

You’ll lose automated advanced filesystem scrubbing, but basic `fsck` on boot still protects you from many issues.

#### 4.4.4. udisks2 (auto-mounting removable drives)

If you never plug USB sticks into your robot at runtime:

```bash
sudo systemctl disable --now udisks2.service
```

#### 4.4.5. Avahi & printing (desktop conveniences)

If you see services like:

- `avahi-daemon.service` (mDNS / .local hostname discovery)
- `cups.service`, `cups-browsed.service` (printing)

You can disable them on a headless robot:

```bash
sudo systemctl disable --now avahi-daemon.service
sudo systemctl disable --now cups.service cups-browsed.service
```

Only keep Avahi if you rely on `.local` hostnames for discovery.

---

## 5. Network Tuning for Faster Boot

Network startup can also delay boot, especially if the system waits for an IP address before proceeding.

### 5.1. Avoid waiting too long for “network-online”

Many services specify:

```ini
After=network-online.target
Wants=network-online.target
```

This can slow boot if `systemd-networkd-wait-online` or similar takes several seconds.

If your robot application can tolerate the network coming up slightly later, use:

```ini
After=network.target
```

instead of `network-online.target` in your own systemd service units.

### 5.2. Use static IP for Wi‑Fi (Ubuntu with Netplan)

If your Pi gets its IP via DHCP, boot can be delayed while waiting for a lease. A static IP makes network bring-up more deterministic.

Edit your Netplan file, e.g.:

```bash
sudo nano /etc/netplan/01-netcfg.yaml
```

Example static Wi‑Fi configuration (adjust to match your network):

```yaml
network:
  version: 2
  wifis:
    wlan0:
      access-points:
        "YourSSID":
          password: "YourPassword"
      dhcp4: no
      addresses: [192.168.1.50/24]
      gateway4: 192.168.1.1
      nameservers:
        addresses: [1.1.1.1,8.8.8.8]
```

Apply the configuration:

```bash
sudo netplan apply
```

Reboot and re-measure boot with `systemd-analyze`.

> **Note:** Details vary if you’re using NetworkManager instead of Netplan/systemd-networkd, but the principle is the same—reduce DHCP delay and unnecessary "wait-online" behavior.

---

## 6. Run Your Robot App as a Systemd Service

To make your robot responsive as soon as possible after boot, run your robot control software as a **systemd service**.

### 6.1. Create a service unit

Assume your robot app entrypoint is `/home/pi/robot/main.py` and it needs basic networking and Bluetooth, but can start without waiting for full "network-online":

Create a new unit file:

```bash
sudo nano /etc/systemd/system/robot.service
```

Example unit:

```ini
[Unit]
Description=Robot control stack
After=bluetooth.target network.target
Wants=bluetooth.target

[Service]
Type=simple
User=pi
WorkingDirectory=/home/pi/robot
ExecStart=/usr/bin/python3 /home/pi/robot/main.py
Restart=on-failure

[Install]
WantedBy=multi-user.target
```

Save and enable it:

```bash
sudo systemctl daemon-reload
sudo systemctl enable robot.service
```

Reboot and verify:

```bash
sudo reboot
# after boot
systemctl status robot.service
```

Your robot stack should now start automatically early in the boot sequence, right after basic networking and Bluetooth are available.

---

## 7. Raspberry Pi–Specific Boot Tweaks

On Ubuntu for Raspberry Pi, the firmware and boot configuration typically live under `/boot/firmware`. On Raspberry Pi OS, they’re usually in `/boot`.

### 7.1. Remove boot delay and splash

Edit the Pi boot configuration:

```bash
sudo nano /boot/firmware/config.txt
```

Add (or adjust) these settings:

```ini
# Don’t delay at boot
boot_delay=0

# Disable the rainbow splash screen (optional)
disable_splash=1
```

If you don’t use the serial console for debugging, you can also disable UART to slightly streamline boot:

```ini
enable_uart=0
```

(Leave `enable_uart=1` if you use serial logs or console.)

### 7.2. Disable unused onboard audio

If your robot doesn’t use the Pi’s onboard audio:

```ini
# In /boot/firmware/config.txt or usercfg.txt
dtparam=audio=off
```

This removes unnecessary audio init.

> **Note:** If you are on Raspberry Pi OS, these settings might go in `/boot/config.txt` instead of `/boot/firmware/config.txt`. The idea is the same.

Reboot and verify that everything still works, then re-run `systemd-analyze` to see the cumulative effect.

---

## 8. Measure Progress and Iterate

After each batch of changes, repeat your measurements:

```bash
systemd-analyze
systemd-analyze blame | head -20
systemd-analyze critical-chain
```

Track:

- **Kernel time** – mainly affected by firmware and kernel; big changes here require kernel/bootloader tweaks or custom images.
- **Userspace time** – the main thing you’re tuning by disabling services and simplifying boot.
- **Which services still dominate** in `systemd-analyze blame`.

Aim for:

- No unnecessary heavyweight services (no `snapd*`, `cloud-init*`, etc. unless you truly need them)
- A **multi-user (text) target** instead of `graphical.target`
- Your robot app running as a **systemd service** started early in the boot process


---

## 9. Going Even Further: Custom Minimal Images

If you need **extreme** boot speed (e.g. a couple of seconds from power-on to robot ready), consider:

- **Buildroot** or **Yocto** to build a custom, minimal Linux image:
  - Stripped-down kernel
  - BusyBox userland
  - Only your robot app + core drivers

This is more complex and beyond the scope of this guide, but the concepts are the same:

1. Minimize services
2. Minimize drivers
3. Start your application as early as possible

For many Raspberry Pi robots, however, a carefully trimmed Ubuntu Server or Raspberry Pi OS Lite using the steps above strikes a great balance between **boot speed**, **maintainability**, and **developer comfort**.

---

## 10. Summary Checklist

Use this quick checklist to turn a stock Pi system into a fast-boot robot controller:

- [ ] Measure baseline with `systemd-analyze`, `blame`, and `critical-chain`
- [ ] Switch to `multi-user.target` (no GUI)
- [ ] Disable Snap (`snapd.service`, `snapd.seeded.service`) if unused
- [ ] Disable Cloud-Init once setup is done
- [ ] Disable ModemManager if no cellular modem is used
- [ ] Optionally disable Apport, Pollinate, e2scrub, udisks2, Avahi, CUPS, etc.
- [ ] Tune networking to avoid long `wait-online` delays (static IPs where possible)
- [ ] Add your robot app as a systemd service that starts after basic network/BT
- [ ] Tweak Pi boot config (no boot delay, optional no splash, optional no audio)
- [ ] Re-measure and iterate until boot time meets your requirements

You can adapt this structure directly into a blog post, README, or project documentation for your robot platform.

