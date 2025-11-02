# `src/` overview

This directory contains everything needed to develop, deploy, and run SpotmicroAI. It has two primary parts:

- `connect_tool/` — a local helper that prepares your development machine, bootstraps a Raspberry Pi (the robot), and deploys code to it.
- `spotmicroai/` — the robot-side application code, configs, runtime controllers, and tools (including the interactive configuration UI).


## What lives in `src/`

- `pyproject.toml` — Python project settings (type checking, tooling, etc.).
- `pyrightconfig.json` — Pyright type-checker configuration.
- `requirements-dev.txt` — local dev-only dependencies for working on this repo.
- `connect_tool/` — setup and deployment utility (runs on your computer).
- `spotmicroai/` — the code that actually runs on the robot (deployed to the Pi).


## `connect_tool/` (local setup and deploy)

The Connect Tool is designed to run on your computer, not on the robot. It makes first-time setup painless and incremental updates fast.

What it does, end-to-end:

1. Local environment readiness (via the repo-level wrapper):
	- Verifies you have Python 3 and pip installed.
	- Creates/uses a local virtual environment at `src/.venv`.
	- Installs development requirements from `src/requirements-dev.txt`.
2. Captures and reuses connection details:
	- Stores the last used hostname and username in `src/connect_tool/connect_config.json`.
	- If a prior connection exists, it reuses those values; otherwise it prompts for hostname, username, and password (with sensible defaults like `spotmicroai.local` and `pi`).
3. SSH and keys:
	- Tests SSH connectivity to the robot.
	- Can generate an SSH key (`~/.ssh/id_rsa`) and install it on the Pi for passwordless logins.
4. First-time robot bootstrap (when it detects a brand new connection):
	- Runs `sudo apt update && sudo apt upgrade -y`.
	- Installs system packages: `python3`, `python3-pip`, `python3-venv`, `python3-dev`, `i2c-tools`, `python3-smbus`.
	- Enables I2C on the Pi.
	- Creates a Python virtual environment on the robot at `~/.venv` and upgrades `pip`.
	- Creates the project directory on the robot: `~/spotmicroai`.
5. Deploys code and gets it ready:
	- Uses `rsync` to copy the local `src/spotmicroai/` folder to `~/spotmicroai` on the robot (with sensible excludes like `__pycache__`, `.venv`, `.git`, logs, etc.).
	- Installs Python dependencies on the robot from `spotmicroai/requirements.txt` into `~/.venv`.
	- Sets executable bits on shell scripts.
	- Launches the SpotmicroAI configuration menu (a curses TUI) on the robot.
6. Subsequent runs (after initial setup):
	- Detects that setup was completed and performs an incremental `rsync` of changes.
	- Optionally relaunches the menu (use `--skip-menu` to just deploy without launching).

Where it keeps state and logs:

- Cached settings: `src/connect_tool/connect_config.json` (committed next to the tool so it’s easy to see/reset).
- Log file: `src/connect_tool/setup.log` (with rotation to `setup.log.1`, etc.).

CLI options (run on your computer):

- `--reset` — forget previous settings and start fresh (also deletes the above JSON file for you).
- `--skip-menu` — deploy without launching the robot’s configuration UI at the end.
- `--verbose` — enable verbose tool output.

How to run it:

Recommended (handles local Python/pip/venv automatically):

```bash
# from repo root
./connect.sh

# examples
./connect.sh --reset       # start fresh, prompt for hostname/user
./connect.sh --skip-menu   # just deploy code updates, don’t launch the TUI
```

Alternative (if you already activated `src/.venv` yourself):

```bash
# from repo root
source src/.venv/bin/activate
python src/connect_tool/connect_tool.py --help
```

Notes and expectations:

- The first run can take several minutes (apt update/upgrade and package installs on the Pi).
- SSH host key checks are disabled during automated steps to keep the flow non-interactive.
- If `spotmicroai.local` doesn’t resolve for you, use the Pi’s IP address as the hostname.


## `spotmicroai/` (robot application)

This is the code that runs on the robot. The Connect Tool deploys this entire folder to `~/spotmicroai` on the Pi and installs its Python dependencies into `~/.venv`.

Highlights:

- `runtime/` — the main entry (`runtime/main.py`) and controllers:
  - `abort_controller/`, `gait_controller/`, `lcd_screen_controller/`, `motion_controller/`, `remote_controller/`, `telemetry_controller/`.
- `hardware/` — hardware drivers and adapters:
  - `servo/` (joint types, angle limits), `lcd_display/` (I2C LCD), `buzzer/`.
- `spot_config/` — the interactive configuration app (TUI) and UI assets.
- `configuration/` — configuration provider, templates, and servo config structures.
- `boot/` — service files and boot-time scripts for installing/running as a service.
- `integration_tests/` — hardware-facing tests and scripts that exercise subsystems.
- `requirements.txt` — Python dependencies installed on the robot.


### Launching the configuration UI on the robot

Once deployed, the Connect Tool will typically start the UI for you. You can also launch it manually over SSH:

```bash
ssh <user>@<hostname>
cd ~/spotmicroai
bash spot_config.sh
```

About the UI (from `spot_config/spot_config.py`):

- Keyboard: arrows or `j`/`k` to navigate, Enter to select, numbers `1-9` for quick select.
- `q` quits, `b` or `ESC` goes back.
- Menus are JSON-driven and can launch commands or submenus.


## Typical workflow

1. Clone the repo on your computer.
2. Power up the Pi (robot) and connect it to your network.
3. From the repo root on your computer, run:

	```bash
	./connect.sh
	```

4. Accept defaults or enter hostname/username/password when prompted.
5. Let the Connect Tool perform the first-time bootstrap on the Pi.
6. When the configuration menu appears on the Pi, use it to proceed with calibration, diagnostics, and other actions.
7. When you change code locally, re-run `./connect.sh` to sync and (optionally) relaunch the menu.


## Troubleshooting

- I can’t connect to `spotmicroai.local`.
  - Use the Pi’s IP address as the hostname.
  - Ensure the Pi and your computer are on the same network.

- I want to start over.
  - Run `./connect.sh --reset` (or delete `src/connect_tool/connect_config.json`).

- The first setup is slow.
  - That’s normal: apt update/upgrade, package installs, and enabling I2C can take time.

- I don’t want the menu to launch after deploy.
  - Use `./connect.sh --skip-menu` (or add `--skip-menu` to the Python invocation).


## Security notes

- The tool can install your SSH public key on the Pi for future passwordless logins.
- Cached settings include hostname/username but not your password.
- Automated SSH steps disable strict host key checking to avoid interactive prompts during setup.


## Where things end up on the Pi

- Project code: `~/spotmicroai`
- Python virtual environment: `~/.venv`
- Launcher for the config UI: `~/spotmicroai/spot_config.sh`


---

If you spot anything that doesn’t match the current behavior of the tool or the runtime, open an issue or a PR—this README is meant to be a concise, up-to-date map of the `src/` anatomy and how to use it.

