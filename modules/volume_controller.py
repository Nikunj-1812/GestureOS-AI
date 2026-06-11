"""
Volume Controller Module for GestureOS AI
=========================================
Manages Windows system volume via pycaw, maps hand distance to volume level,
smooths volume adjustments, and logs changes.
"""

import math
from datetime import datetime
from loguru import logger

class VolumeController:
    """Controls system volume based on thumb-pinky distance using pycaw."""

    def __init__(
        self,
        min_distance_px: float = 30.0,
        max_distance_px: float = 250.0,
        smoothing: float = 0.15,
    ) -> None:
        self.min_distance = min_distance_px
        self.max_distance = max_distance_px
        self.smoothing = smoothing

        self.last_volume_pct = -1.0  # Float tracking current volume percentage (0.0 to 100.0)
        self.last_logged_pct = -1    # Integer tracking last logged volume percentage (0 to 100)
        self._volume = None

        self._initialize_pycaw()

    def _initialize_pycaw(self) -> None:
        """Initialize the pycaw audio controller on Windows."""
        try:
            from ctypes import cast, POINTER
            from comtypes import CLSCTX_ALL, CoInitialize
            from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume

            # Initialize COM libraries
            try:
                CoInitialize()
            except Exception:
                pass

            devices = AudioUtilities.GetSpeakers()
            if devices is not None:
                if hasattr(devices, "EndpointVolume"):
                    self._volume = devices.EndpointVolume
                else:
                    interface = devices.Activate(IAudioEndpointVolume._iid_, CLSCTX_ALL, None)
                    self._volume = cast(interface, POINTER(IAudioEndpointVolume))
                
                # Sync initially with the current OS system volume level
                curr_scalar = self._volume.GetMasterVolumeLevelScalar()
                self.last_volume_pct = curr_scalar * 100.0
                self.last_logged_pct = int(round(self.last_volume_pct))
                logger.info(f"VolumeController initialized. Synced with system volume: {self.last_logged_pct}%")
        except Exception as e:
            logger.warning(f"Could not initialize Windows pycaw interface: {e}. Fallback to simulated volume mode.")

    def get_current_volume(self) -> int:
        """Returns the current volume percentage, syncing with system volume if possible."""
        if self._volume is not None:
            try:
                from comtypes import CoInitialize
                CoInitialize()
                curr_scalar = self._volume.GetMasterVolumeLevelScalar()
                self.last_volume_pct = curr_scalar * 100.0
                return int(round(self.last_volume_pct))
            except Exception:
                pass
        return int(round(max(0.0, self.last_volume_pct)))

    def update_volume(self, distance_px: float) -> tuple[int, bool]:
        """
        Updates the volume based on the measured hand distance.
        
        Maps distance to volume: min_distance -> 0%, max_distance -> 100%.
        Smooths using an Exponential Moving Average (EMA) and sets OS volume.
        
        Returns:
            (volume_percentage, has_changed)
        """
        # Map distance to raw volume level [0.0, 100.0]
        if distance_px <= self.min_distance:
            raw_pct = 0.0
        elif distance_px >= self.max_distance:
            raw_pct = 100.0
        else:
            raw_pct = ((distance_px - self.min_distance) / 
                       (self.max_distance - self.min_distance)) * 100.0

        # Apply EMA smoothing
        if self.last_volume_pct < 0.0:
            self.last_volume_pct = raw_pct
        else:
            self.last_volume_pct = (self.last_volume_pct * (1.0 - self.smoothing) + 
                                    raw_pct * self.smoothing)

        # Clamp volume level
        self.last_volume_pct = max(0.0, min(100.0, self.last_volume_pct))
        int_pct = int(round(self.last_volume_pct))

        # Set system volume using pycaw if available
        if self._volume is not None:
            try:
                from comtypes import CoInitialize
                CoInitialize()
                self._volume.SetMasterVolumeLevelScalar(int_pct / 100.0, None)
            except Exception as e:
                logger.error(f"Failed to set Windows system volume: {e}")

        # Check for integer change to log without spamming every frame
        changed = (int_pct != self.last_logged_pct)
        if changed:
            self.last_logged_pct = int_pct
            logger.info(f"[{datetime.now().strftime('%H:%M:%S.%f')[:-3]}] [VOLUME] {int_pct}%")

        return int_pct, changed
