"""
GestureOS AI — Dashboard Launcher
===================================
Run this file to start the CustomTkinter dashboard:

    python run_dashboard.py

Requirements:
    pip install customtkinter==5.2.2
"""

import os
import sys
from pathlib import Path

# Suppress third-party logging / console spam (MediaPipe, TensorFlow, OpenCV)
os.environ['GLOG_minloglevel'] = '2'
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '2'
os.environ['OPENCV_LOG_LEVEL'] = 'ERROR'
os.environ['OPENCV_FFMPEG_LOGLEVEL'] = '-8'

# Ensure project root is on sys.path so dashboard package is importable
sys.path.insert(0, str(Path(__file__).parent))

from dashboard.app import main

if __name__ == "__main__":
    main()
