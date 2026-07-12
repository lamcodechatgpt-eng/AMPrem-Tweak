#import <Foundation/Foundation.h>
#import <StoreKit/StoreKit.h>
#import <objc/runtime.h>

// ==========================================
// 1. BYPASS STOREKIT INVALID IDENTIFIERS
// ==========================================
%hook SKProductsResponse
- (NSArray<NSString *> *)invalidProductIdentifiers {
    // Luôn trả về mảng rỗng để chống lỗi 21008/00000
    return @[];
}
%end

// ==========================================
// 2. BYPASS RECEIPT VALIDATION (INAPPRECEIPT)
// ==========================================
// Nếu ứng dụng sử dụng Kvitto hoặc InAppReceipt để check offline
%hook InAppReceipt
- (BOOL)isValid {
    return YES;
}
- (BOOL)verify {
    return YES;
}
- (BOOL)verifyHash {
    return YES;
}
- (BOOL)verifySignature {
    return YES;
}
%end

// ==========================================
// 3. RUNTIME HOOK: KÍCH HOẠT PREMIUM CHO MỌI CLASS
// ==========================================
static BOOL alwaysTrue(id self, SEL _cmd) {
    return YES;
}

static BOOL alwaysFalse(id self, SEL _cmd) {
    return NO;
}

__attribute__((constructor))
static void global_premium_hook() {
    int numClasses = objc_getClassList(NULL, 0);
    Class *classes = (Class *)malloc(sizeof(Class) * numClasses);
    objc_getClassList(classes, numClasses);
    
    for (int i = 0; i < numClasses; i++) {
        Class cls = classes[i];
        if (!cls) continue;
        
        // Kích hoạt isPremiumUser
        Method m1 = class_getInstanceMethod(cls, NSSelectorFromString(@"isPremiumUser"));
        if (m1) {
            method_setImplementation(m1, (IMP)alwaysTrue);
        }
        
        // Kích hoạt hasPremium
        Method m2 = class_getInstanceMethod(cls, NSSelectorFromString(@"hasPremium"));
        if (m2) {
            method_setImplementation(m2, (IMP)alwaysTrue);
        }
        
        // Vô hiệu hóa isFreeUser
        Method m3 = class_getInstanceMethod(cls, NSSelectorFromString(@"isFreeUser"));
        if (m3) {
            method_setImplementation(m3, (IMP)alwaysFalse);
        }
        
        // Kích hoạt Subscription_started
        Method m4 = class_getInstanceMethod(cls, NSSelectorFromString(@"subscription_started"));
        if (m4) {
            method_setImplementation(m4, (IMP)alwaysTrue);
        }
    }
    free(classes);
}
