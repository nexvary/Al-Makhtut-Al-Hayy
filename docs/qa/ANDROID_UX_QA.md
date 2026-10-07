# Android UX QA Gate

This checklist is required before distributing a test APK.

## Navigation
- Home opens.
- Add Book opens and Back returns to Home.
- About opens and Back returns to Home.
- Settings opens and Back returns to Home.
- Local PDF reader opens and both toolbar Back and system Back return to Home.
- Local image/IIIF reader opens and both Back paths work.
- Remote manuscript reader opens and both Back paths work.
- No internal page intentionally exits the app.

## Add Book
- PDF picker is wired to local import.
- Multi-image picker is wired to local import.
- HTTPS IIIF manifest import is wired to the IIIF parser.
- Imported books appear in My Books and open immediately.

## Layout
- Bottom navigation uses four standard Material icons at normal touch-target sizes.
- No text is placed over navigation icons.
- Reader controls are separated into top/bottom bars.
- Screens use responsive Compose layouts and safe insets.
- Arabic, Persian and Urdu use RTL through Android locale/layout direction.

## Languages
Arabic, English, Turkish, Spanish, German, Italian, French, Urdu, Persian and Russian are declared in localeConfig and have localized core UI strings.

## About / links
- Website: https://nexvary.com/
- Facebook: https://www.facebook.com/share/14p9krEn5ij/
- Email: mailto:info@nexvary.com
- YouTube: https://www.youtube.com/@NexvaryInc
- X: https://x.com/Nexvary
All buttons use ACTION_VIEW and reject unsupported URI schemes.

## Android compatibility
- minSdk 26.
- targetSdk 36.
- compileSdk 36.
- Android 15 (API 35) is within the supported target range.
- Production cleartext HTTP is disabled; debug-only local API traffic is explicitly overridden.

## Automated checks
Android CI runs unit tests for navigation contracts, social-link URI schemes, the requested language set, and then builds the debug APK.


## Stability gate added 2026-10-04
Android CI now requires `testDebugUnitTest`, `lintDebug` and `assembleDebug`.
API 35 instrumentation runs on a 360×640 dp viewport in English and Arabic.
Offline fixtures cover a two-page PDF, multiple images, persisted library, page
navigation, pinch zoom with reachable controls, system/internal Back, invalid PDF
cleanup, IIIF v2/v3 parsing and scrolling to the final Add Book control.
The Storage Access Framework picker itself, provider availability, remote reader,
network image loading and all social-link handlers still require further coverage.
Imported files are capped at 128 MiB each; image batches at 500 pages. Failed
imports remove partial directories; library updates use AtomicFile under a shared
lock. Original imported files are copied, never changed.


## IIIF recovery correction — 0.1.5

Phone screenshots showed HTTP 429 on import and blank/failed Gallica page images despite a valid 245-page library record. Manifest loading previously issued an immediate second request after 429/403, and image rendering had no progress or retry controls. The new shared metadata/image client stops at 403, respects Retry-After seconds/date (60-second fallback), and prevents requests to the same host during cooldown. A three-entry/15-minute in-memory manifest cache and reuse of existing IIIF imports avoid repeated metadata requests.

IIIF full-image display requests use a 1600-pixel-wide preview while the stored original URL remains unchanged. Images use the same identifiable client headers, bounded 16 MiB transfers and sampled decoding, with a 64 MiB app-cache limit. Failed pages show HTTP status, a localized explanation and a retry control/countdown. Successful cached pages can be reopened without the network. Local PDF/image readers remain separate.

On 2026-10-07, live GET of the supplied Gallica manifest returned 200 with 245 pages. Standard IIIF preview GETs for f1, f6 and f11 returned 200/image-jpeg and valid images (934765, 132130, 505526 bytes). An earlier request returned 403, demonstrating that availability is not guaranteed for every request/device/network. This check does not prove the user's mobile network is unblocked. Android regression tests cover 429 -> cooldown -> manual retry -> rendered image, offline cache reuse and explicit 403 UI; current release CI must pass before delivery.
