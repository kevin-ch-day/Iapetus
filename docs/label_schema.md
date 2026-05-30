# Label Schema Notes

Rendered labels are human-readable display/export artifacts.
Structured fields remain source-of-truth in records.

## Malware

Pattern:

```text
platform:malware_primary.family-variant:[subtype]
```

Example:

```text
AndroidOS:Trojan.Anubis-t:[Banker]
```

## Normal Android app

Pattern:

```text
platform:app_name-build_ref:[app_category]
```

Example:

```text
AndroidOS:Facebook-64543615:[SocialMedia]
```

## Implementation notes

- `platform`, `malware_primary`, `family`, `variant`, `app_name`, `build_ref`,
  `subtype`, and `app_category` are structured fields.
- Renderers provide exactly formatted strings for exports and logs.
