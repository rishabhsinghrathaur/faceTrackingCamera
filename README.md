# 🎥 Face Tracking Camera for Classrooms

An intelligent, Arduino-based camera system that automatically tracks and follows a teacher's face during lectures. Uses computer vision to detect the teacher and smoothly pan the camera to keep them centered in frame.

![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)
![OpenCV](https://img.shields.io/badge/OpenCV-4.11-green.svg)
![Arduino](https://img.shields.io/badge/Arduino-Uno-red.svg)

## 📋 Features

- **Automatic Face Tracking**: Real-time face detection and servo control
- **Smooth Panning**: Exponential smoothing filter eliminates servo jitter
- **Auto-Detection**: Automatically finds your Arduino serial port
- **Multi-Face Support**: Optional recognition of multiple authorized faces
- **Status LED**: Arduino LED shows tracking state (solid=tracking, off=searching)
- **Search Mode**: Servo scans when face is lost, resumes tracking when found
- **Configurable**: YAML-based configuration for all parameters
- **Cross-Platform**: Works on Windows, Linux, and macOS
- **Well-Documented**: Complete setup guides and troubleshooting

## 🎯 How It Works

1. **Camera captures** video frames at 15 FPS
2. **Face detection** finds all faces in the frame using `face_recognition`
3. **Recognition** compares against stored teacher face encoding
4. **Servo control** calculates angle to center the teacher's face
5. **Arduino moves** the servo smoothly via serial communication
6. **Search mode** activates if teacher leaves frame for >1 second

Result: Camera automatically follows the teacher as they move around the classroom!

## 🛠️ Hardware Requirements

### Electronics
- **Arduino Uno** (or compatible board)
- **Servo motor** (standard SG90 or better, metal gear recommended)
- **Webcam** (any USB webcam, 640x480 @ 30fps minimum)
- **USB cable** to connect Arduino to computer
- **5V power supply** (optional if using servo only, can power from Arduino)

### Wiring

```
Arduino Pin 9  ----> Servo signal wire (orange/yellow)
Arduino 5V     ----> Servo power wire (red)
Arduino GND    ----> Servo ground wire (black)
```

**⚠️ Important**: High-torque servos may draw too much current from Arduino's 5V regulator.
For larger servos, use an external 5V power supply:
```
External 5V +  ----> Servo red wire
External 5V GND + Arduino GND ----> Servo black wire
```

See `hardware/README.md` for detailed wiring diagrams and diagrams.

## 🚀 Quick Start

### 1. Install Dependencies

**Linux/macOS:**
```bash
chmod +x scripts/install.sh
./scripts/install.sh
source venv/bin/activate
```

**Windows:**
```cmd
scripts\install.bat
venv\Scripts\activate
```

Or manually:
```bash
python3 -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Connect Hardware

1. Connect servo to Arduino (Pin 9, 5V, GND)
2. Connect Arduino to computer via USB
3. Upload `track.ino` to Arduino (see below)
4. Mount camera on servo (use proper mounting bracket!)

### 3. Upload Arduino Code

Open Arduino IDE and upload `track.ino`:
```bash
arduino-cli compile --fqbn arduino:avr:uno track.ino
arduino-cli upload -p /dev/ttyUSB0 --fqbn arduino:avr:uno track.ino
```

Or use the Arduino IDE GUI:
- Open `track.ino`
- Select Tools > Board: Arduino Uno
- Select correct Port
- Click Upload

### 4. Calibrate Servo

Find the correct servo angle range for your camera mount:

```bash
python scripts/run.py calibrate
```

The servo will sweep full range. Observe the camera movement and note the angles where it hits physical limits. Enter those values when prompted.

### 5. Capture Teacher's Face

```bash
python scripts/run.py capture
```

- Position yourself in the camera view
- Press SPACE when ready
- Face encoding saves to `models/teacher_face.pkl`

**Tips:**
- Capture in good lighting
- Keep neutral expression
- Capture from slightly different angles for robustness
- Remove glasses if you normally don't wear them

### 6. Run Face Tracking!

```bash
python scripts/run.py track
```

You should see:
- Video window with tracking guide
- Servo moves to follow your face
- Green bounding box when teacher detected
- Status text: "TRACKING: teacher" or "SEARCHING"
- Blue center line and tolerance zone

**Controls:**
- `q` - Quit tracking
- Ensure only teacher's face is visible during tracking

## ⚙️ Configuration

Edit `config.yaml` to customize:

### Camera Settings
```yaml
camera:
  index: 1              # Camera device (0, 1, etc.)
  width: 640            # Frame width
  height: 480           # Frame height
  fps: 15               # Lower = less CPU
  flip_horizontal: true  # Mirror view
```

### Tracking
```yaml
tracking:
  tolerance: 0.5        # Face recognition strictness (lower = stricter)
  smoothing_alpha: 0.4  # Servo smoothness (0=slow, 1=fast)
  center_tolerance: 40  # Pixels from center to tolerate
  scanning_speed: 2     # Search mode servo speed
```

### Servo
```yaml
servo:
  default_min: 30       # Left limit (from calibration)
  default_max: 150      # Right limit (from calibration)
  center_angle: 90      # Center position
```

### Debug
```yaml
debug:
  show_video: true      # Show preview window
  show_fps: true        # Show FPS counter
  log_level: "INFO"     # DEBUG, INFO, WARNING, ERROR
```

## 📚 Script Commands

### `scripts/run.py` - Main CLI

```bash
# Show help
python scripts/run.py --help

# List commands
python scripts/run.py --help

# Capture face(s)
python scripts/run.py capture                    # Single face
python scripts/run.py capture --multi           # Multiple faces
python scripts/run.py capture --names Alice Bob  # Named faces

# Run tracking (all options override config)
python scripts/run.py track
python scripts/run.py track --camera 0 --port /dev/ttyUSB0 --tolerance 0.4
python scripts/run.py track --no-video          # Headless mode

# Calibrate servo
python scripts/run.py calibrate

# List hardware
python scripts/run.py cameras    # Show available cameras
python scripts/run.py ports      # Show available serial ports
```

### Standalone Scripts

```bash
# Direct capture
python -m src.face_capture --help

# Direct tracking
python -m src.face_tracker --camera 1 --port auto --tolerance 0.5
```

## 🔧 Troubleshooting

### Camera not found
```bash
python scripts/run.py cameras
```
Check index, ensure camera not used by another app.

### Arduino not found
```bash
python scripts/run.py ports
```
- Check USB connection
- Install Arduino drivers (Windows)
- Use `--port` to specify manually
- Linux: Add user to `dialout` group: `sudo usermod -a -G dialout $USER`

### Face not recognized
- Capture in better lighting
- Lower `tolerance` in config (0.4-0.6 range)
- Recapture face with different angles
- Remove glasses/hats

### Servo jittery
- Increase `smoothing_alpha` (0.5-0.8)
- Check power supply (use external 5V for large servos)
- Ensure servo rated for camera weight

### High CPU usage
- Lower `camera.fps` to 10 or 15
- Reduce `camera.width/height`
- Use headless mode (`--no-video`)
- Consider using a Raspberry Pi for dedicated deployment

### Import errors
```bash
# Make sure venv is activated
source venv/bin/activate  # Linux/Mac
venv\Scripts\activate      # Windows

# Reinstall requirements
pip install -r requirements.txt
```

## 📁 Project Structure

```
faceTrackingCamera/
├── src/
│   ├── __init__.py
│   ├── config_loader.py   # YAML config management
│   ├── camera.py          # Camera capture and utilities
│   ├── servo_controller.py # Arduino serial + smoothing
│   ├── face_recognizer.py # Face loading and comparison
│   ├── face_capture.py    # Capture command entry point
│   └── face_tracker.py    # Main tracking loop
├── scripts/
│   ├── run.py             # Unified CLI with subcommands
│   ├── calibrate.py       # Servo calibration tool
│   ├── install.sh         # Linux/Mac installer
│   ├── install.bat        # Windows installer
│   └── test_setup.py      # Setup verification
├── models/
│   └── teacher_face.pkl   # Saved face encodings
├── hardware/
│   └── README.md          # Wiring diagrams and components
├── docs/
│   └── calibration.md     # Calibration guide
├── config.yaml            # Main configuration
├── requirements.txt       # Python dependencies
├── track.ino              # Arduino firmware
├── .gitignore
└── README.md              # This file
```

## 🔬 Advanced Usage

### Multiple Faces

Modify `config.yaml`:
```yaml
faces:
  multi_face: true
  names: ["teacher", "admin"]
```

Then capture multiple:
```bash
python scripts/run.py capture --multi --names teacher admin
```

The system will recognize any of the stored faces and log which one was detected.

### Headless Operation

For deployment on a Raspberry Pi or server:

```bash
python scripts/run.py track --no-video --log_level INFO
```

Logs will be saved to `logs/face_tracker.log`.

### Custom Recognition Tolerance

Adjust based on your environment:
- `0.3-0.4`: Very strict (few false positives)
- `0.5-0.6`: Balanced (recommended)
- `0.7-0.8`: Very loose (may recognize wrong person)

Set via config or command line:
```bash
python scripts/run.py track --tolerance 0.4
```

## 🤝 Contributing

Contributions welcome! Please:
1. Fork the repository
2. Create a feature branch
3. Make changes with clear comments
4. Test on your hardware
5. Submit a pull request

## 📝 License

This project is open source. Please attribute appropriately.

## 🙏 Credits

- Built with [face_recognition](https://github.com/ageitgey/face_recognition) by Adam Geitgey
- Uses OpenCV for image processing
- Arduino for servo control

## 📧 Support

Open an issue on GitHub for bugs, feature requests, or questions!

---

**Happy tracking!** 🎯
