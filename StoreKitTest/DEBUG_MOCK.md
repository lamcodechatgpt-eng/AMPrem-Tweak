# Debug-only Premium mock

`DebugPremiumEntitlement.swift` is a source-level test seam, not an IPA patch.

## Add it safely

1. Add the file to the development/test target only.
2. Keep the target's normal `SWIFT_ACTIVE_COMPILATION_CONDITIONS` containing
   `DEBUG`.
3. Keep the Release target out of the file's target membership, or verify the
   `#if DEBUG` block is not compiled.
4. When testing, set the launch environment variable
   `DEBUG_PREMIUM_MOCK=1` in the Xcode scheme.
5. Inject `PremiumEntitlementFactory.makeProductionSafe(default:)` into the
   feature under test.

Without the launch flag, the factory returns the real entitlement provider even
in a Debug build. The mock is intentionally limited to a set of feature benefit
strings and does not fake StoreKit receipts, App Store transactions, or backend
licenses.

## Release guard

The implementation is wrapped in `#if DEBUG`, so Release compilation removes
the symbols. Do not add this file to the production target and do not copy it
into an IPA bundle.

## Crash fix artifact

The binary load-command fix is separate:

[AlightMotion_Premium_clean_fixed.ipa](</D:/iPA/Alightmotion/AlightMotionMod/V1/AlightMotion_Premium_clean_fixed.ipa>)

That artifact has no `AlightMotionCrack.dylib` reference. It must still be
re-signed before installation.

## Verify a real entitlement

Use `PremiumRuntimeProbe.swift` in an authorized development target when you
need to distinguish a verified StoreKit transaction from a UI flag or injected
library. Treat Premium as active only when both `isVerified == true` and
`isActive == true`.
