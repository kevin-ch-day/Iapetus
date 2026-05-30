# Android Knowledge Seed Notes

This note captures authoritative Android facts used by Iapetus seed knowledge (self-contained only).

## Core Android facts tracked by the knowledge layer

- **Manifest ownership**: every Android app project includes an `AndroidManifest.xml` describing package identity,
  components, permissions, and compatibility.
- **Declared components**: manifest must declare activities, services, broadcast receivers, and content providers.
- **Permissions in manifest**: permissions that protect sensitive data or behavior are declared via manifest tags.
  Android distinguishes install-time and runtime permissions, with runtime prompts introduced by the runtime model.
- **SDK compatibility**: `uses-sdk` includes `minSdkVersion`/`targetSdkVersion` attributes used by the package manager during install.
- **Signing**: Android apps must be signed, and newer signature schemes (v2+) validate APK integrity across the full APK payload.
- **APK structure**: APKs are ZIP-like archives with `AndroidManifest.xml`, `classes.dex`, resources, assets, libraries, and `META-INF` metadata.

## Seed concept additions in this pass

- `android_runtime`: runtime context, process and component lifecycle framing.
- `apk_signing`: seed evidence for integrity and trust checks.
- `android_components`: manifest components, intent filters, and lifecycle hooks.

## Seed synthetic data

- `iapetus knowledge data` to list available synthetic topics.
- `iapetus knowledge data android_apps` for small app-entity samples.
- `iapetus knowledge data permission_levels` for permission-level examples.
- `iapetus knowledge data dataset_rows` for shape-matching row samples.
- `iapetus knowledge teach` for lesson-oriented sequencing.

## Suggested future seed data sources (not connected now)

- Manifest-derived static labels/features
- Permission declaration parsing
- Signature / signing-block metadata
- Component graph extraction

## Reference links (official docs used for structure)

- Android app manifest overview: https://developer.android.com/guide/topics/manifest/manifest-intro.html
- Uses-permission element: https://developer.android.com/guide/topics/manifest/uses-permission-element
- Uses-sdk compatibility attributes: https://developer.android.com/guide/topics/manifest/uses-sdk-element
- Permissions overview: https://developer.android.com/guide/topics/permissions/overview
- APK signing: https://source.android.com/docs/security/features/apksigning
- APK signing scheme v2: https://source.android.com/docs/security/features/apksigning/v2
- APK signing scheme v3: https://source.android.com/docs/security/features/apksigning/v3
- APK signing scheme v4: https://source.android.com/docs/security/features/apksigning/v4
- Network security config: https://developer.android.com/training/articles/security-config
- App bundle format: https://developer.android.com/guide/app-bundle/app-bundle-format

Iapetus uses these facts to keep the seed deterministic and training-oriented without live integrations.
