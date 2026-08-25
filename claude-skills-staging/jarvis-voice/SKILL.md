---
name: jarvis-voice
description: Use when working on JARVIS voice input/output — speech-to-text, text-to-speech, wake word, push-to-talk, and microphone/speaker handling. Providers must be swappable (faster-whisper for STT, Piper for TTS, pyttsx3 as fallback) and must never block the GUI. Triggers include "voice", "speech", "STT", "TTS", "wake word", "hey jarvis", "microphone", "listen", "speak", "talk". Load with jarvis-core and jarvis-agent.
---

# JARVIS Voice

Voice is an *interface* into the same agent, not a separate brain. See jarvis-core and jarvis-agent.

## Architecture

```text
Microphone → Speech-to-text → Agent → Response → Text-to-speech → Speaker
```

## Provider abstractions (swappable)

```python
class SpeechToText:
    def listen(self) -> str: ...
class TextToSpeech:
    def speak(self, text: str) -> None: ...
```

Keep concrete engines behind these interfaces so they can be replaced, exactly like the LLM provider (jarvis-llm).

## Engines

- STT: **faster-whisper** (local, lightweight) preferred.
- TTS: **Piper** (local) preferred; **pyttsx3** as a simple fallback.

Prefer local/offline engines for privacy and to avoid per-call latency and cost. Choose small models to fit the 8 GB / integrated-GPU target (see jarvis-performance).

## Activation

- **Push-to-talk** is the primary, always-available mode.
- **Wake word** ("Hey JARVIS") is optional and must not be mandatory. After activation, show a "Listening…" state and process the request.

## Status & settings

Expose microphone status, speaker status, and voice settings (engine, voice, rate). Indicate clearly when the mic is active (privacy — jarvis-security).

## Non-blocking

STT/TTS run off the GUI thread (jarvis-gui, jarvis-performance). Make responses interruptible where practical.

## Error handling

Missing microphone, no audio device, STT failure, or TTS failure must degrade gracefully with a friendly message — never crash. Fall back to text I/O when audio is unavailable.

## Definition of done

STT/TTS behind swappable interfaces, push-to-talk works, wake word optional, mic activity indicated, runs off the GUI thread, failures handled, and interfaces covered by tests with mocked audio (see jarvis-testing).
