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
- Reader-owned state preserves the question while scrolling the original image into view. Changing page/region clears the question and prior result; coroutine cancellation prevents a previous request from replacing the new scope. The client rejects evidence for another source and verified records without a reviewer.
- A bounded HTTP transport limits metadata responses to 2 MiB, uses connection/read timeouts and closes connections. Network/parser failures remain retryable.
- Local PDF/image/IIIF readers continue without a backend. Living layers and the lab require a configured backend; their controls do not imply offline inference.
- Instrumentation protocol fixtures use Android JSON parsing; compact-phone UI fixtures exercise layer history, unknown confidence, region selection, missing evidence, page reset and Back. These complement the real API/browser integration tests; they do not claim a native live-server or physical-device test.
- Accessibility uses content descriptions, native controls, RTL-capable layouts and semantic headings.

## Ottoman reader and Academy

The remote reader has a collapsed Ottoman Lab panel with separately selectable layout, HTR,
transcription, transliteration, modernization and Arabic/English translation histories.
Dictionary results retain review/source metadata; unverifiable etymology is rejected by the client.
Reviewed, rights-recorded exercises support an attempt followed by progressive reveal. Exercise
feedback is explicitly educational, not scholarly verification. No automatic translator or full
curriculum is bundled. Native fixtures test stage display, dictionary and zero/one-step reveal.

## Heritage hub

Home links to a native source-backed knowledge hub: entity search, reviewed corpus excerpts,
Gregorian time filtering and museum exhibitions/objects. Reconstruction carries an explicit
interpretive label and assumptions. Geographic points can open OpenStreetMap; no embedded
historical basemap is claimed. Source links resolve the actual manuscript/page/region and
open the original reader; Back returns to the hub. Missing source/network errors are visible.
The reader source may be a fixture in instrumentation; live server journeys run in web CI.
