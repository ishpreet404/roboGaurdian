# 1080p Camera & FPS Performance Guide

## Changes Made

### Pi Camera Server (pi_camera_server.py)
- **Resolution**: Upgraded from 640x480 to **1920x1080 (Full 1080p)**
- **FPS**: Set to 30 FPS (standard for stability)
- **JPEG Quality**: Reduced to 45% (from 50%) to handle larger frames efficiently
- **Codec**: Added MJPEG codec for better 1080p compression
- **Auto Settings**: Enabled auto-exposure and auto-focus for better image quality

### Windows AI Controller (windows_ai_controller.py)
- **Display Size**: Smart scaling to 960x540 (half of 1080p for performance)
- **Display FPS**: Increased to 25 FPS for smoother 1080p viewing
- **Memory**: Optimized for handling larger frames

## FPS vs Model Performance Analysis

### Higher FPS Benefits for AI Model:
✅ **More Training Data**: More frames = more detection opportunities
✅ **Better Tracking**: Smoother object movement tracking
✅ **Faster Response**: Quicker detection of new objects entering frame
✅ **Reduced Motion Blur**: Less blur in fast-moving scenarios
✅ **Better Temporal Consistency**: Smoother detection history

### Higher FPS Drawbacks:
❌ **Increased CPU Load**: More frames to process
❌ **Network Bandwidth**: Larger data transmission requirements
❌ **Memory Usage**: More frame buffers needed
❌ **Heat Generation**: More processing = more heat

## Performance Optimization Strategy

### Current Setup (Optimized):
- **Camera FPS**: 30 FPS (good balance)
- **AI Inference**: Every 6th frame (5 FPS) - prevents overload
- **Display FPS**: 25 FPS (smooth viewing)
- **Stream Quality**: 45% JPEG (balance quality vs performance)

### FPS Recommendations:

#### For Maximum Model Performance:
```python
# Pi Camera Settings
self.fps = 60              # Higher FPS for more data
self.inference_skip_frames = 12  # Process every 12th frame (5 FPS inference)
```

#### For Maximum Quality:
```python
# Pi Camera Settings  
self.fps = 30              # Standard FPS
self.jpeg_quality = 70     # Higher quality
self.inference_skip_frames = 3   # Process every 3rd frame (10 FPS inference)
```

#### For Battery/Low Power:
```python
# Pi Camera Settings
self.fps = 15              # Lower FPS to save power
self.inference_skip_frames = 3   # Process every 3rd frame (5 FPS inference)
```

## Testing Different FPS Settings

### To Test Higher FPS:
1. Edit `pi_camera_server.py`:
   ```python
   self.fps = 60  # Try 60 FPS
   ```

2. Edit `windows_ai_controller.py`:
   ```python
   self.inference_skip_frames = 12  # Process every 12th frame
   ```

3. Monitor performance:
   - Watch CPU usage
   - Check network bandwidth
   - Monitor model accuracy
   - Observe tracking smoothness

### Performance Monitoring:
- **Pi CPU**: Should stay below 80%
- **Network**: Monitor for dropped frames
- **Windows CPU**: Watch AI processing load
- **Memory**: Check for memory leaks with higher resolution

## Recommendations:

### Current 1080p/30fps Setup:
- **Best for**: General use, good quality, stable performance
- **Pros**: High resolution, stable FPS, manageable processing load
- **Cons**: Higher bandwidth than 720p

### If You Want to Try 60fps:
1. Good internet connection required (1080p60 = ~10-15 Mbps)
2. Monitor Pi temperature (may need cooling)
3. Watch for frame drops
4. AI model will get more data points (potentially better tracking)

### Sweet Spot Recommendation:
- **Camera**: 1080p @ 30 FPS (current setup)
- **AI Processing**: Every 6th frame (5 FPS inference)
- **Display**: 25 FPS (smooth viewing)

This gives you high-quality video with efficient AI processing and good responsiveness!