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
