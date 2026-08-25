---
name: jarvis-vision
description: Use when implementing JARVIS vision — screenshot capture and analysis by a vision-capable model, plus OpenCV camera work (face/presence detection, gesture recognition, optional head pose and eye tracking). The camera is strictly opt-in and remote image analysis must be indicated in the UI. Triggers include "screenshot", "what's on my screen", "camera", "OpenCV", "face detection", "gesture", "vision", "analyze image". Load with jarvis-core and jarvis-security; jarvis-study builds on this.
---

# JARVIS Vision

Two distinct domains, both exposed as registered tools (jarvis-tools):

1. **Screenshot analysis** — capture the screen and send it to a vision-capable model for explanation (e.g. "what is this error?").
2. **Local camera processing** — OpenCV for face/presence detection, gestures, and optional head pose / eye tracking.

## Camera is opt-in

The camera is **never** activated silently. It is off by default, enabled explicitly by the user, and its active state is shown in the UI (jarvis-security, jarvis-gui). The same applies to any recording.

## Screenshot workflow

```text
take_screenshot → vision model → image analysis → explanation
```

The vision provider is configurable, like the LLM (jarvis-llm). When an image is sent to a **remote** provider, indicate it clearly (privacy — jarvis-security). Prefer redacting obvious sensitive regions when feasible.

## Tools

```text
take_screenshot | analyze_screenshot | camera_status
```

Camera capabilities (detection, gestures) are added as further registered tools.

## Performance

Avoid continuous processing unless a feature explicitly needs it. Throttle frame rate, process at reduced resolution, and release the camera/handles when done. Camera processing must be configurable and lightweight for the integrated-GPU target (jarvis-performance).

## Honest capabilities

Report only measurable signals (a face is/ isn't detected, eyes open/closed, head yaw/pitch). Do not claim to infer subjective states like "interest." See jarvis-study for the focus/attention use case.

## Definition of done

Screenshot and camera features exposed as registered tools, camera opt-in with a visible active indicator, remote image analysis indicated, processing throttled and resources released, and tests using mocked frames/screenshots (see jarvis-testing).
