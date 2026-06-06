# GestureOS AI

A computer vision system for real-time gesture recognition and OS interaction using deep learning.

## Project Structure

```
GestureOS_AI/
├── assets/                  # Static assets (icons, images, fonts, sounds)
├── config/                  # App and model configuration files
├── data/                    # Raw, processed datasets and annotations
├── models/                  # Model architectures and saved weights
├── modules/                 # Core CV, AI, and gesture processing logic
├── ui/                      # User interface (GUI/overlay components)
├── tests/                   # Unit and integration tests
├── logs/                    # Runtime logs
├── scripts/                 # Utility and automation scripts
├── main.py                  # Application entry point
├── requirements.txt         # Python dependencies
└── .env.example             # Environment variable template
```

## Getting Started

```bash
# 1. Create and activate virtual environment
python -m venv .venv
.venv\Scripts\activate        # Windows
source .venv/bin/activate     # Linux/macOS

# 2. Install dependencies
pip install -r requirements.txt

# 3. Run the application
python main.py
```

## Requirements
- Python 3.9+
- Webcam or external camera
- See requirements.txt for full dependency list
