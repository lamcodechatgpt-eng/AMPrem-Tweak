# Product ID validation

## Observed values

The original Alight Motion executable contains only these subscription
prefixes:

```text
alightcreative.motion.1w_
alightcreative.motion.1m_
alightcreative.motion.1y_
```

The complete value `alightcreative.motion.1y_t60_1w` was found in injected
crack/tweak dylibs and in this local test file. Static analysis cannot prove
that it is a current App Store Connect product.

## What counts as valid

- For local Xcode StoreKit Testing: any syntactically valid ID declared in the
  active `.storekit` file is valid for that local session.
- For App Store sandbox/production: the ID must exist in the publisher's
  App Store Connect product catalog, belong to the matching app, and be in a
  state available to the test account/storefront.

## How to finalize for an authorized app

1. Open the app's App Store Connect record.
2. Copy the Product ID exactly, including case and punctuation.
3. Replace `productID` in `PremiumTest.storekit`.
4. Replace `PremiumStoreTests.productID`.
5. Select `PremiumTest.storekit` in the Xcode scheme's Run > Options.
6. Run the product-loading test before testing purchase/restore.

Do not infer a production Product ID from a crack dylib, error message, or
binary prefix. A local transaction is not valid in an App Store-signed build.
