"""
Gait Controller - Wraps SpotMicroWalkController in queue-based controller pattern.

Runs the gait walking controller at fixed frequency and listens for velocity commands
from the remote controller via queue.
"""

import queue
import time

from spotmicroai.logger import Logger
from spotmicroai import labels
from spotmicroai.runtime.gait_controller.gait_service import GaitService
from spotmicroai.runtime.gait_controller.models import SpotMicroNodeConfig, Command
from spotmicroai.runtime.gait_controller.inverse_kinematics_solver import InverseKinematicsSolver

log = Logger().setup_logger('Gait Controller')


class GaitController:
    """Wraps SpotMicroWalkController in the queue-based controller pattern.

    Runs the gait controller at a fixed frequency (50Hz by default) and processes
    velocity commands from other controllers via queue.
    """

    def __init__(self, communication_queues):
        """Initialize gait controller with configuration and kinematics.

        Args:
            communication_queues (dict): Dictionary of inter-controller queues.
        """
        self.queues = communication_queues
        self.cfg = SpotMicroNodeConfig.defaults()

        # Initialize kinematics
        self.kinematics = InverseKinematicsSolver()

        self.controller = GaitService(
            config=self.cfg,
            kinematics=self.kinematics,
        )

        # Current command (updated via queue)
        self.current_command = Command(x_vel_cmd=0.0, y_vel_cmd=0.0, yaw_rate_cmd=0.0)
        self.is_running = False
        self.has_received_commands = False  # Only write to servos after receiving first command

        log.info(labels.GAIT_INITIALIZED)

    def do_process_events_from_queue(self):
        """Main loop: process commands and step gait at fixed frequency.

        Runs the gait controller at cfg.dt intervals (0.02 seconds = 50Hz) while
        continuously checking for new velocity commands from the queue.
        """
        log.info(labels.GAIT_STARTED)
        self.is_running = True

        last_step_time = time.time()

        try:
            while self.is_running:
                # Non-blocking check for new commands
                try:
                    message = self.queues['gait_controller'].get(block=False)
                    self._handle_command(message)
                except queue.Empty:
                    # Queue is empty, continue with current command
                    pass

                # Step gait at fixed frequency (cfg.dt = 0.02 seconds = 50Hz)
                current_time = time.time()
                elapsed = current_time - last_step_time

                if elapsed >= self.cfg.dt:
                    try:
                        self.controller.step(self.current_command)

                        # TODO: Publish body state to telemetry for visualization
                        # body_state = self.controller.body_state
                        # self.queues['telemetry_controller'].put({
                        #     'source': 'gait_controller',
                        #     'body_position': {
                        #         'x': body_state.coordinate.x,
                        #         'y': body_state.coordinate.y,
                        #         'z': body_state.coordinate.z,
                        #     },
                        #     'phase_index': self.controller.phase_index,
                        # })

                    except Exception as e:
                        log.error(labels.GAIT_STEP_ERROR.format(e))

                    last_step_time = current_time

                # Small sleep to prevent busy-waiting
                time.sleep(0.001)

        except KeyboardInterrupt:
            log.info(labels.GAIT_INTERRUPTED)
        except Exception as e:
            log.error(labels.GAIT_ERROR.format(e))
        finally:
            self.is_running = False
            log.info(labels.GAIT_STOPPED)

    def _handle_command(self, message):
        """Process incoming command message.

        Args:
            message (dict): Command message with velocity parameters.
        """
        try:
            if isinstance(message, dict):
                if 'x_vel_cmd' in message or 'y_vel_cmd' in message or 'yaw_rate_cmd' in message:
                    self.current_command = Command(
                        x_vel_cmd=message.get('x_vel_cmd', self.current_command.x_vel_cmd),
                        y_vel_cmd=message.get('y_vel_cmd', self.current_command.y_vel_cmd),
                        yaw_rate_cmd=message.get('yaw_rate_cmd', self.current_command.yaw_rate_cmd),
                    )
                    self.has_received_commands = True
                    self.controller.write_to_servos = True  # Enable servo writes
                    log.debug(labels.GAIT_COMMAND_UPDATED.format(self.current_command))

                elif message.get('action') == 'stop':
                    self.current_command = Command(0.0, 0.0, 0.0)
                    self.controller.write_to_servos = False  # Disable servo writes on stop
                    log.info(labels.GAIT_COMMAND_STOP)

                elif message.get('action') == 'exit':
                    self.is_running = False
                    self.controller.write_to_servos = False
                    log.info(labels.GAIT_SHUTTING_DOWN)

        except Exception as e:
            log.error(labels.GAIT_COMMAND_ERROR.format(e))
