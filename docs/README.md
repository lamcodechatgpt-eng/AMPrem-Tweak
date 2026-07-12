# Alight Motion Premium Mod - Research Notes

## Project Structure
- `scripts/` - All Python analysis & build scripts
- `docs/` - Research findings
- `Payload/` - App bundle (extracted IPA contents)
- `extracted/` - Original extracted IPA backup
- `*.ipa` - Built IPA files

## Key Findings

### IAPManager Class
- Swift class, stored ObjC class_ro_t at file 0x2F419C0 (metaclass, flags=0x81)
- Mangled name: `_TtC12AlightMotion10IAPManager` at 0x289DA20
- Field records at __swift5_fieldmd + 0x34054 (file 0x2BDAC34): 8 fields
- instanceStart=0x28, instanceSize=0x28

### IAPManager Fields (offsets relative to instanceStart 0x28)
| Offset | Type | Name |
|--------|------|------|
| +0x00 | ref | applePayContextProvider |
| +0x08 | ref | motionContextProvider |
| +0x10 | Bool | isSpooner |
| +0x11 | Bool | isFreeUser |
| +0x12 | Bool | isPremiumUser |
| +0x13 | u8 | experiments |
| +0x14 | Bool | isDataCollectionEnabled |
| +0x18 | ref | presentedPaywalls |

### Key Getters
- **isPremiumUser getter** at 0x18F81D8: `ldrb w0,[x0,#0x3A]; ret` → patched to `mov w0,#1`
- Vtable reference at 0x24E09E8 → 0x18F81D8
- 42 total reads of isPremiumUser (+0x3A)

### All Read Counts (using mask 0xFFFFFC00)
- isPremiumUser (+0x3A): 42 reads
- isFreeUser (+0x39): 106 reads
- experiments (+0x3B): 31 reads
- isSpooner (+0x38): 729 reads

### IAPError Enum
- Error 21008 = `IAPError.invalidIdentifiers`
- Error strings at:
  - 0x289D8A0: '21009 (Product List Empty)'
  - 0x289D8C0: '21008 (Invalid Identifiers: ['
  - 0x289D8E0: '21007 (Invalid Task)'
- Error 21008 is constructed via Swift enum metadata, NOT via MOVZ/MOVK

### Error Construction Function
- Function at 0x12B9E68 (called from BL at 0x0008DACC)
- Contains switch on w7:
  - w7 <= 1: checks w27; if w27!=0 → error 21008, else → error 21006
  - w7 == 3: error 21023 (App Store Connection Error)
  - w7 == 4: error 21022 (Server Error)
  - w7 == 2 (default): loads from data table
- Function at 0x12BAFD4 called from 0x12BA0B4 to construct actual error object

### v16 Patches
1. All 42 isPremiumUser reads → mov w?, #1
2. All 106 isFreeUser reads → mov w?, #0
3. All 31 experiments reads → mov w?, #1
4. NOP BL at 0x0008DACC (prevents error construction function from running)
5. MOVK at 0x12BA040: 21008 → 21000 (backup)
6. CBNZ at 0x12BA018: NOP'd (backup)

### Installation
- IPA must be sideloaded via LiveContainer
- LiveContainer re-signs on installation (no _CodeSignature issues)
- StoreKitTestCertificate.cer replaced with AppleIncRootCertificate.cer

## Build Versions
- v1-v7: Initial exploration, various patch approaches
- v8: First Bool getter patches (4 addresses, offsets 0x21-0x24)
- v9-v12: Iterating on patch approach
- v13: All 42 isPremiumUser reads corrected (mask 0xFFFFFC00)
- v14: Added 106 isFreeUser=0 + 31 experiments=1
- v15: Added error 21008 CBNZ NOP + MOVK change
- v16: NOP BL to error construction function at 0x0008DACC + all v15 patches

## To Investigate Further
- Why error 21008 persists despite patches (maybe different code path)
- Monetization classes (BSPMonetization, EntitlementsRefresher)
- Product IDs from Firebase Cloud Functions (Oracle)
- Receipt validation via InAppReceipt
