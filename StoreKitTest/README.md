# StoreKit Test setup

This directory contains a local StoreKit configuration for development testing.
It does not modify an IPA and its transactions are not valid in production.

## Requirements

- A macOS machine with a current Xcode release.
- An editable Xcode project for the app being tested.
- A development build and, for physical devices running iOS 16 or later,
  Developer Mode enabled.

## Add the configuration

1. Drag `PremiumTest.storekit` into the Xcode project navigator and enable
   **Copy items if needed**.
2. Open **Product > Scheme > Edit Scheme**.
3. Select **Run > Options**.
4. Set **StoreKit Configuration** to `PremiumTest.storekit`.
5. Build and run the development target from Xcode.

The local configuration defines this auto-renewable annual subscription:

`alightcreative.motion.1y_t60_1w`

This is a local test identifier copied from the workspace's injected test
components. The scan did not find it as a verified App Store Connect product
in the original executable. It is valid only inside this local `.storekit`
file; it is not evidence of a production product owned by the app publisher.

For a real development project, replace `productID` in this file and
`PremiumStoreTests.productID` with the exact Product ID from that project's
App Store Connect account. The identifier requested by application code must
match the local configuration exactly.

## Test a Premium purchase manually

1. Start the app from Xcode with the configuration active.
2. Open the app's purchase screen and select the annual product.
3. Confirm the StoreKit test payment sheet.
4. In Xcode, choose **Debug > StoreKit > Manage Transactions**.
5. Verify that the subscription appears and that the app observes a verified
   transaction through `Transaction.currentEntitlements` or
   `Transaction.updates`.

Use the transaction manager to expire, revoke, refund, interrupt, or delete the
test transaction. Deleting transactions resets the local purchase history.

## Add the automated tests

1. Add `PremiumStoreTests.swift` to an XCTest target.
2. Add `PremiumTest.storekit` to the test target.
3. Run the tests on an iOS simulator or development device.

The sample tests cover product loading, an active verified entitlement, and an
expired subscription. The app should derive Premium state only from a verified,
unrevoked, unexpired transaction.

## Receipt validation

StoreKit Testing in Xcode creates locally signed receipts. If the app validates
StoreKit 1 receipts itself, export the local public certificate from Xcode using
**Editor > Save Public Certificate**, include it only in the development target,
and select it with a `DEBUG` build condition. Production builds must continue to
use Apple's production certificate and normal App Store validation.

To stop local testing, return to **Run > Options** and set
**StoreKit Configuration** to **None**.
