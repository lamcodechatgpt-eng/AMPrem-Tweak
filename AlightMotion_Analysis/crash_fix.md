# Crash fix record

## Confirmed cause

The source IPA contained this load command in the main Mach-O:

`@rpath/AlightMotionCrack.dylib`

The archive did not contain
`Payload/AlightMotion.app/Frameworks/AlightMotionCrack.dylib`. This is a
deterministic dyld launch failure, not an uncertain Premium-state issue.

## Fixed artifact

[AlightMotion_Premium_clean_fixed.ipa](</D:/iPA/Alightmotion/AlightMotionMod/V1/AlightMotion_Premium_clean_fixed.ipa>)

The repair:

- Removes the stale weak dylib load command from the 64-bit Mach-O.
- Removes any injected `AlightMotionCrack.dylib` member if present.
- Removes `AlightMotion_patched` duplicate executable.
- Removes the app-level `_CodeSignature` and `SC_Info` metadata so a sideload
  signer can create a fresh signature.
- Keeps the original app executable and functional resources.

## Verification

- ZIP integrity: passed (`testzip() = None`).
- Main executable remains Mach-O 64-bit (`cffaedfe`).
- `ncmds`: 121 → 120.
- `sizeofcmds`: 13,152 → 13,096.
- Stale dylib reference: absent.
- Injected dylib file: absent.
- Duplicate patched executable: absent.
- App-level old signature/SC_Info: absent.
- Output size: 134,111,065 bytes.
- IPA SHA-256: `906C7CEC329FB018070F761409493E9DB0200F5E634CE161040FBD9E36AD0E84`.
- Full verifier: ZIP, bundle metadata, 5 Mach-O binaries, system/app RPATH
  resolution and injection-artifact scan all passed.

The output must be signed again before installation. This fixed artifact is a
stable non-injected build; it does not attempt to bypass Premium entitlement.
