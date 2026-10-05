# Android Architecture

The Android client is a native Kotlin/Jetpack Compose reader.

- Target SDK: 36.
- Production cleartext HTTP is disabled; the debug manifest permits local emulator development.
- The list/detail flow reads the same API schema as the web app.
- `ZoomablePage` provides pinch zoom/pan and source-region overlays.
- Region cards expose machine/draft/verified layers.
- Android TextToSpeech provides optional Arabic audio.
- `OfflineCache` is a local JSON metadata cache. Image caching remains rights-aware.
- The remote reader loads append-only living-layer history for the current page and filters it to the selected region (or whole-page scope).
- Manuscript AI Lab calls `/api/v1/ai-lab/ask` with explicit manuscript/page/region, task and optional translation language. It displays sourced excerpts, review state, confidence (including unknown), reviewer, witness and revision. Missing evidence is explicit; no generative provider is bundled.
- Changing page/region clears the question and prior result; coroutine cancellation prevents a previous request from replacing the new scope. The client rejects evidence for another source and verified records without a reviewer.
- A bounded HTTP transport limits metadata responses to 2 MiB, uses connection/read timeouts and closes connections. Network/parser failures remain retryable.
- Local PDF/image/IIIF readers continue without a backend. Living layers and the lab require a configured backend; their controls do not imply offline inference.
- Instrumentation protocol fixtures use Android JSON parsing; compact-phone UI fixtures exercise layer history, unknown confidence, region selection, missing evidence, page reset and Back. These complement the real API/browser integration tests; they do not claim a native live-server or physical-device test.
- Accessibility uses content descriptions, native controls, RTL-capable layouts and semantic headings.
