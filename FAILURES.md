## F1: Gemini TTS 429 rate limit
- What broke: 429 Too Many Requests on narration after ~5 calls in a row.
- What I tried: retries with 1-2 s backoff (too short, failed).
- Fix: 25 s increasing backoff on 429, 15 s pacing between calls, per-shot caching so finished shots are never re-requested.
- Also: API key leaked into the error URL, so I rotated it and moved the key to a request header.

## F2: FFmpeg/ffprobe not found on Windows
- What broke: FileNotFoundError when running ffprobe.
- Fix: installed FFmpeg (winget / pacman), reopened the terminal.