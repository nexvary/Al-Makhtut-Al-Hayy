# Android Architecture

The Android client is a native Kotlin/Jetpack Compose reader.

- Target SDK: 36.
- Production cleartext HTTP is disabled; the debug manifest permits local emulator development.
- The list/detail flow reads the same API schema as the web app.
- `ZoomablePage` provides pinch zoom/pan and source-region overlays.
- Region cards expose machine/draft/verified layers.
- Android TextToSpeech provides optional Arabic audio.
- `OfflineCache` is a local JSON metadata cache. Image caching remains rights-aware.
- Ask-the-manuscript calls the grounded retrieval endpoint and displays evidence excerpts.
- Accessibility uses content descriptions, native controls, RTL-capable layouts and semantic headings.
