# 🎯 Servo Calibration Guide

Detailed guide for calibrating your servo to match your specific camera mount setup.

## Why Calibration?

Every servo and camera mount is different:
- Servo horns may have slight misalignment
- Camera weight distribution varies
- Mounting position affects rotation range
- Physical stops may differ from servo's 0-180° range

**Without calibration:**
- Camera might rotate too far and hit mechanical stops
- Tracking may be off-center
- Servo may strain against limits
- Teacher may go out of frame at edges

**With calibration:**
- Precise control within safe range
- Centered tracking behavior
- No wasted movement outside visible area
- Longer servo lifespan

## 📊 Understanding Servo Angles

```
    0° ─────────────── 90° ─────────────── 180°
   (Full CCW)      (Center)         (Full CW)
       ⬆                             ⬆
    Left limit                   Right limit
   Camera view               Camera view
   points left               points right
```

**Important**: The `0°`-`180°` scale is relative to servo's internal potentiometer.
Your camera's actual field of view (FOV) depends on:
- Servo mounting position
- Camera lens focal length
- Mounting distance from rotation axis

Typically:
- 90° = camera pointing straight ahead
- <90° = camera pointing left
- \>90° = camera pointing right

## 🛠️ Calibration Process

### Step 1: Initial Setup

1. Mount camera securely on servo
2. Connect servo to Arduino (Pin 9)
3. Upload `track.ino` to Arduino
4. Connect Arduino to computer
5. Ensure `config.yaml` exists with defaults

### Step 2: Auto-Calibration (Recommended)

```bash
python scripts/run.py calibrate
```

**What happens:**
1. Servo sweeps from 0° to 180° continuously
2. Observe camera movement range
3. Press ENTER when servo reaches approximate left limit
4. Servo stops, enter your observed left angle
5. Enter observed right angle
6. Servo tests the new limits
7. Optionally run a quick tracking test
8. Values automatically saved to `config.yaml`

**Example output:**
```
==================================================
 SERVO CALIBRATION WIZARD
==================================================

Goal: Find the servo angles where your camera's left and right limits occur.

Current config limits:
  min_angle: 30
  max_angle: 150

--- Enter new limits ---
Minimum angle (left limit) [30]: 25
Maximum angle (right limit) [150]: 155

✅ Calibration saved to config.yaml
   servo.default_min: 25
   servo.default_max: 155
```

### Step 3: Manual Calibration (Alternative)

Edit `config.yaml` directly:

```yaml
servo:
  center_angle: 90
  default_min: 30   # Left angle where camera view hits left wall
  default_max: 150  # Right angle where camera view hits right wall
```

Then test with:
```bash
python scripts/run.py track --smoothing 1.0
```
(Set smoothing to 1.0 for direct response during testing)

Adjust `default_min` and `default_max` until:
- Camera pans comfortably within usable range
- No binding or forcing at any angle
- Teacher stays in frame at edges

### Step 4: Verify with Tracking Test

1. Run tracking: `python scripts/run.py track`
2. Stand at left side of camera view
3. Verify camera tracks you without hitting left limit
4. Move to right side
5. Verify camera tracks without hitting right limit
6. If camera loses you at edges, adjust limits outward
7. If camera jams or servo strains, adjust limits inward

## 🎛️ Fine-Tuning Tips

### Adjusting Center Point

If camera doesn't point straight ahead at `servo.center_angle`:

```yaml
servo:
  center_angle: 95  # Slightly right (increase to point more right)
  # or
  center_angle: 85  # Slightly left
```

**How to determine correct `center_angle`:**
1. Stand directly in front of camera where you want "center"
2. Run tracking and observe what servo angle the camera settles at
3. Set `center_angle` to that value

### Adjusting Smoothing

Higher smoothing = slower, smoother movement
Lower smoothing = faster, more responsive

```bash
python scripts/run.py track --smoothing 0.6
```

Recommended range:
- **0.3 - 0.5**: Active tracking, moderate smoothing
- **0.5 - 0.7**: Smooth tracking (default 0.4)
- **0.7 - 0.9**: Very smooth, slower response

If servo is jittery, increase smoothing.
If servo feels laggy, decrease smoothing.

### Tolerance Zone

The `center_tolerance` defines how far from center the face can be before servo moves:

```yaml
tracking:
  center_tolerance: 40  # pixels
```

Higher = less servo movement (teacher can drift more before correction)
Lower = more precise centering (more servo movement)

## 📈 Calibration Scenarios

### Scenario 1: Servo Horn 180° Opposite

**Problem**: Camera points left when servo at 90°, right at smaller angles.

**Solution**: Reverse servo horn orientation or adjust `center_angle`:
```yaml
servo:
  center_angle: 0   # If 0° = straight ahead
```

Alternatively, physically reverse the servo horn attachment.

### Scenario 2: Camera FOV Too Narrow

**Problem**: Teacher goes out of frame at extreme angles before servo reaches mechanical limit.

**Solution**: This is normal. You've already hit the camera's optical limit, not the servo's. Adjust `default_min/max` to match camera FOV, not servo mechanical stops.

### Scenario 3: Servo Whines at Limits

**Problem**: Servo straining at `min_angle` or `max_angle`.

**Solution**: Move limits inward:
```yaml
servo:
  default_min: 40   # Was 20
  default_max: 140  # Was 160
```

Servo should move freely without excessive current draw.

### Scenario 4: Tracking Always Off-Center

**Problem**: Servo centers but teacher is consistently left or right of center in frame.

**Solution**: Adjust `center_angle` until camera naturally points where teacher stands. This is a mechanical/optical alignment issue, not software.

## 🔍 Advanced: Multi-Point Calibration

For non-linear response (servo doesn't move linearly with angle), implement a lookup table:

```python
# In face_tracker.py, replace angle calculation
def map_angle(face_offset):
    # face_offset: -width/2 to +width/2
    # Map to servo angle range nonlinearly
    if face_offset < -100:
        angle = config.servo.default_min
    elif face_offset > 100:
        angle = config.servo.default_max
    else:
        # Linear interpolation
        t = (face_offset + 100) / 200
        angle = config.servo.default_min + t * (config.servo.default_max - config.servo.default_min)
    return angle
```

## 📋 Calibration Checklist

Before considering calibration complete:

- [ ] Camera panning is smooth from left to right
- [ ] No binding or servo strain at any angle in range
- [ ] Teacher stays in frame at left and right extremes
- [ ] Tracking centers correctly when teacher stands in front
- [ ] Values saved to `config.yaml`
- [ ] Tracking runs reliably without adjusting mid-session
- [ ] Servo doesn't drift or creep when idle

## 🔄 Recalibration

Re-run calibration if:
- You change the camera mount
- Use a different servo motor
- Move the entire setup to a different location
- Change camera model (different FOV)
- Notice tracking consistently off

## 🎓 Troubleshooting

| Symptom | Likely Cause | Fix |
|---------|-------------|-----|
| Servo hits stop before edge of view | `default_min/max` too narrow | Increase range toward mechanical limits |
| Camera goes past edge of view before servo stops | `default_min/max` too wide | Decrease range |
| Camera doesn't move at all | `center_angle` set outside visible range | Set to mid of `min`-`max` |
| Servo shakes/vibrates | Inadequate smoothing or unstable camera | Increase `smoothing_alpha`, secure camera mounting |
| Tracking drifts slowly | `min_servo_speed` too low | Increase to 1.0 or higher |

## 📚 Reference

- **Default values**: `min_angle=0`, `max_angle=180` (full servo range)
- **Recommended starting point**: `min_angle=30`, `max_angle=150` (for typical wall mounts)
- **Adjustment step**: 5° increments when fine-tuning
- **Final precision**: 1° increments if needed

---

**Remember**: Good calibration enables smooth, reliable tracking!
