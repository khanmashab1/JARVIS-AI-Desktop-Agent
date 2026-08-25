---
name: jarvis-study
description: Use when building the JARVIS study-monitor feature — presence detection, eye-closure and head-orientation signals, focus/Pomodoro timers, study statistics, and spoken (English/Urdu) reminders. It builds on vision (camera signals), voice (reminders), and memory (stats); all thresholds are configurable. Triggers include "study monitor", "focus", "Pomodoro", "eye closure", "attention", "am I studying", "keep me focused". Load with jarvis-core, jarvis-vision, jarvis-voice, and jarvis-security.
---

# JARVIS Study Assistant

A focus/study monitor composed from existing capabilities: camera signals from jarvis-vision, spoken reminders from jarvis-voice, and statistics stored via jarvis-memory. It adds no new low-level system access of its own.

## Features

```text
Eye-closure detection | Head orientation | Presence detection
Focus timer | Pomodoro | Study statistics | Voice reminders
```

## Measurable signals only

Use objective signals: eye-closure duration, head yaw/pitch beyond a threshold, and presence/absence. **Do not** claim to determine whether the user is "interested," motivated, or engaged — those are not measurable from a camera. Frame everything in terms of the concrete signal.

## Example reminders (English/Urdu)

```text
Eyes closed too long → "Uth jao, aankhein kholo aur parhai par focus karo."
Looking away        → "Idhar udhar na dekho, parhai par focus karo."
```

Reminders are spoken through the voice layer; keep tone supportive, not punishing (well-being).

## Configurable thresholds

Every threshold is user-configurable: eye-closure seconds before a reminder, look-away angle and duration, presence-timeout, reminder frequency/cooldown, and Pomodoro work/break lengths. Ship sensible defaults.

## Constraints

Camera is opt-in and its active state is visible (jarvis-security, jarvis-vision). Processing is throttled and lightweight; do not run heavy detection continuously beyond what the feature needs (jarvis-performance). All camera/timer work stays off the GUI thread (jarvis-gui).

## Definition of done

Signals derived from measurable camera data, thresholds configurable with defaults, reminders delivered via the voice layer, stats persisted via memory, camera opt-in and indicated, lightweight processing, and logic covered by tests with mocked signals (see jarvis-testing).
