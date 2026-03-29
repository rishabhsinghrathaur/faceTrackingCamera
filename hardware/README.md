# 🔌 Hardware Setup Guide

Complete guide for building the Face Tracking Camera hardware.

## 📦 Components List

### Required

| Component | Qty | Notes |
|-----------|-----|-------|
| Arduino Uno (or compatible) | 1 | ATmega328P based board |
| Servo motor | 1 | SG90 (plastic gear) or MG996R (metal gear, more torque) |
| Webcam | 1 | Any UVC-compatible webcam, 640x480 @ 30fps minimum |
| USB cable (A to B) | 1 | For connecting Arduino to computer |
| Jumper wires | 3+ | Male-to-male or male-to-female |

### Optional but Recommended

- **Servo mounting bracket**: To securely attach servo to camera
- **External 5V power supply**: For high-torque servos (>2kg/cm)
- **On/off switch**: For the external power supply
- **Project enclosure**: To protect Arduino and wires
- **Tripod mount**: Standard 1/4"-20 tripod screw to mount setup

## 🔧 Wiring Diagram

```
       ┌─────────────┐
       │   Arduino   │
       │     Uno     │
       │             │
       │    5V ──────┼───┐
       │    GND ─────┼───┤
       │   Pin 9 ────┼───┼──→ Servo Signal (yellow/orange)
       └─────────────┘   │
                         │   ┌──────────┐
                         └───┤ SERVO    │
                             │  5V ────┼───┐
                             │  GND ───┼───┼
                             │ Signal ─┘   │
                             └──────────┘  │
                                           │
                                ┌──────────┘
                                │
                         ┌──────┴──────┐
                         │   Webcam    │
                         │   (USB)     │
                         └─────────────┘
```

### Pin Connections

| Arduino Pin | Servo Wire | Color |
|-------------|------------|-------|
| 5V | Power | Red |
| GND | Ground | Black |
| 9 | Signal | Yellow/Orange |

**⚠️ Power Considerations:**

Standard small servos (SG90) can be powered directly from Arduino's 5V pin.
However, when moving or under load, they can draw 200-500mA which may cause
voltage sag and Arduino resets.

**If you experience resets or erratic behavior:**
1. Use an external 5V power supply (2A minimum)
2. Connect external 5V to servo's power wire
3. Connect external GND to Arduino GND **and** servo GND
4. Use a capacitor (100-470µF) across servo's power terminals

```plaintext
External 5V ──┬──> Servo Red
              ├──> Servo Black
              │
         [Capacitor]
              │
              └───> Arduino 5V (optional, NOT to power Arduino!)
```

## 🔩 Mounting the Servo to Camera

### Method 1: Hot Glue / Epoxy (Permanent)

1. **Plan placement**: Determine servo position relative to camera
   - Top mount: Servo above camera, horn pointing down
   - Bottom mount: Servo below camera
   - Side mount: Servo beside camera

2. **Prepare surfaces**:
   - Clean both servo and camera surfaces with alcohol
   - Lightly sand for better adhesion

3. **Attach servo**:
   - Apply hot glue/epoxy to servo body
   - Press firmly onto camera
   - Hold until set (2-3 minutes for hot glue, 24h for epoxy)

4. **Attach camera to servo horn**:
   - Use small screws through camera's tripod mount holes
   - Or use strong double-sided tape
   - Ensure camera is centered on servo horn

5. **Test movement**:
   - Rotate servo full range
   - Check for binding or excessive camera weight on one side
   - Rebalance if needed

### Method 2: 3D-Printed Bracket

If you have CAD skills or access to Printables/Thingiverse:

- Search for "servo camera mount" or "PTZ mount"
- Print bracket with appropriate screw holes
- Bolt servo and camera securely

**Recommended design parameters:**
- Servo horn centered
- Camera weight distributed evenly
- Adjustable tilt angle optional

## 🔌 Serial Connection (Serial Port)

### Windows
1. Connect Arduino via USB
2. Open Device Manager
3. Look under "Ports (COM & LPT)"
4. Note the COM port number (e.g., COM3)
5. Update `config.yaml`:
   ```yaml
   serial:
     port: "COM3"
   ```
   Or use command line: `--port COM3`

### Linux
1. Connect Arduino via USB
2. Check detected device:
   ```bash
   ls /dev/ttyACM*
   ls /dev/ttyUSB*
   ```
3. Usually `/dev/ttyACM0` or `/dev/ttyUSB0`
4. Update `config.yaml`:
   ```yaml
   serial:
     port: "/dev/ttyACM0"
   ```
5. **Permissions**: Add user to `dialout` group:
   ```bash
   sudo usermod -a -G dialout $USER
   ```
   Log out and back in.

### macOS
1. Connect Arduino via USB
2. Check port:
   ```bash
   ls /dev/cu.usbmodem*
   ls /dev/cu.usbserial*
   ```
3. Use the device path (e.g., `/dev/cu.usbmodem14201`)
4. Update `config.yaml` accordingly

## 🧪 Testing the Setup

### 1. Verify Arduino Connection
```bash
python scripts/run.py ports
```
Should list your serial port.

### 2. Upload Test Sketch
In Arduino IDE, upload a simple sweep sketch:
```cpp
#include <Servo.h>
Servo myservo;
void setup() {
  myservo.attach(9);
}
void loop() {
  for (int angle = 0; angle <= 180; angle++) {
    myservo.write(angle);
    delay(15);
  }
  for (int angle = 180; angle >= 0; angle--) {
    myservo.write(angle);
    delay(15);
  }
}
```
Servo should sweep smoothly from 0° to 180° and back.

### 3. Test Camera
```bash
python3 -c "import cv2; cap = cv2.VideoCapture(1); ret, frame = cap.read(); print('OK' if ret else 'FAIL'); cap.release()"
```
Replace `1` with camera index.

### 4. Run Calibration
```bash
python scripts/run.py calibrate
```
Follow the prompts. Servo should move as instructed.

## 📐 Calculating Servo Limits

The `calibrate.py` tool automates this, but here's the manual method:

1. **Center position**: Servo at 90° (camera straight ahead)
2. **Left limit**: Rotate servo counterclockwise until camera hits wall/obstruction
   - Note the angle value (e.g., 30)
   - This is `default_min`
3. **Right limit**: Rotate servo clockwise until camera hits opposite wall
   - Note the angle value (e.g., 150)
   - This is `default_max`

**Save to config.yaml**:
```yaml
servo:
  default_min: 30
  default_max: 150
  center_angle: 90
```

## 🎯 Mounting Tips for Best Tracking

1. **Camera FOV**: Mount so camera's field of view covers typical teacher movement
2. **Servo centering**: Start with 90° and adjust `center_angle` if needed
3. **Clear line of sight**: No obstructions in servo's rotation range
4. **Sturdy mounting**: Avoid wobble or servo stalls
5. **Power**: Use external 5V for anything beyond SG90 micro servo
6. **Cable management**: Prevent USB/servo cables from snagging during rotation

## 🧰 Troubleshooting Hardware

| Problem | Solution |
|---------|----------|
| Arduino not detected | Check USB cable, try different port, install drivers |
| Servo jittery | Check power supply, add capacitor, use external 5V |
| Arduino resets | Under-voltage! Use external power or lower servo current |
| Camera doesn't move | Verify Pin 9 connection, check `track.ino` uploaded |
| Servo stalls | Camera too heavy, use stronger servo or counterweight |
| Intermittent tracking | Check USB connection, servo wiring loose |

## 🔋 Power Supply Recommendations

### Option A: Arduino 5V (for small servos only)
```
Arduino 5V ──> Servo Red
Arduino GND ─> Servo Black
```
Risk: May cause Arduino to reset if servo draws >500mA

### Option B: External 5V (recommended)
```
External 5V ──> Servo Red (direct)
External GND ─┐
              ├─> Servo Black
              └─> Arduino GND (common ground)
```
**Important**: Connect all GNDs together!

Use a 5V USB charger or DC adapter (2A minimum).

## 🛡️ Safety & Best Practices

- 🔌 Always disconnect power before adjusting wiring
- 🔧 Don't over-tighten servo screws (can strip gears)
- 🌡️ Monitor servo temperature - excessive heat indicates overload
- ⚡ Use fuses on external power supplies
- 📏 Keep wires away from servo gears
- 🔄 Test in safe area before permanent installation

## 📚 Further Reading

- [Arduino Servo Library](https://www.arduino.cc/en/Reference/Servo)
- [Face Recognition Documentation](https://face-recognition.readthedocs.io/)
- [OpenCV Python Tutorials](https://docs.opencv.org/master/d6/d00/tutorial_py_root.html)

---

Need help? Open an issue on GitHub!
