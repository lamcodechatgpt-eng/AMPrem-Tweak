#import <objc/runtime.h>
#import <objc/message.h>
#import <Foundation/Foundation.h>
#import <StoreKit/StoreKit.h>
#import <UIKit/UIKit.h>

#pragma mark - Helpers
static BOOL returnYes(id self, SEL _cmd) { return YES; }
static BOOL returnNo(id self, SEL _cmd) { return NO; }

/// Try patching a selector on a specific class; returns YES if patched
static BOOL patchSelectorOnClass(Class cls, NSString *selName, IMP impl) {
    if (!cls) return NO;
    Method m = class_getInstanceMethod(cls, NSSelectorFromString(selName));
    if (!m) return NO;
    const char *types = method_getTypeEncoding(m);
    if (!types) return NO;
    while (*types && isdigit(*types)) types++;
    if (types[0] == 'c' || types[0] == 'B') {
        method_setImplementation(m, impl);
        return YES;
    }
    return NO;
}

/// Try patching a class method selector
static BOOL patchClassSelectorOnClass(Class cls, NSString *selName, IMP impl) {
    if (!cls) return NO;
    Method m = class_getClassMethod(cls, NSSelectorFromString(selName));
    if (!m) return NO;
    method_setImplementation(m, impl);
    return YES;
}

#pragma mark - 1. AMProxyProtocol — intercept Oracle / license endpoint
@interface AMProxyProtocol : NSURLProtocol <NSURLSessionDataDelegate, NSURLSessionTaskDelegate>
@property (nonatomic, strong) NSURLSessionDataTask *task;
@property (nonatomic, strong) NSMutableData *responseData;
@property (nonatomic, strong) NSURLResponse *response;
@end

@implementation AMProxyProtocol

+ (BOOL)canInitWithRequest:(NSURLRequest *)request {
    if ([NSURLProtocol propertyForKey:@"AMProxyHandled" inRequest:request]) return NO;
    NSString *url = request.URL.absoluteString;
    if ([url containsString:@"getAccountStatusAndLicenses"]) return YES;
    if ([url containsString:@"oracle.bendingspoons"]) return YES;
    return NO;
}

+ (NSURLRequest *)canonicalRequestForRequest:(NSURLRequest *)request { return request; }

- (void)startLoading {
    NSMutableURLRequest *newRequest = [self.request mutableCopy];
    [NSURLProtocol setProperty:@YES forKey:@"AMProxyHandled" inRequest:newRequest];
    self.responseData = [NSMutableData data];
    NSURLSession *session = [NSURLSession sessionWithConfiguration:[NSURLSessionConfiguration defaultSessionConfiguration] delegate:self delegateQueue:nil];
    self.task = [session dataTaskWithRequest:newRequest];
    [self.task resume];
}

- (void)stopLoading { [self.task cancel]; self.task = nil; }

- (void)URLSession:(NSURLSession *)session dataTask:(NSURLSessionDataTask *)dataTask didReceiveResponse:(NSURLResponse *)response completionHandler:(void (^)(NSURLSessionResponseDisposition))completionHandler {
    self.response = response;
    completionHandler(NSURLSessionResponseAllow);
}

- (void)URLSession:(NSURLSession *)session dataTask:(NSURLSessionDataTask *)dataTask didReceiveData:(NSData *)data { [self.responseData appendData:data]; }

- (void)URLSession:(NSURLSession *)session task:(NSURLSessionTask *)task didCompleteWithError:(NSError *)error {
    if (error) {
        [self.client URLProtocol:self didFailWithError:error];
        return;
    }
    NSString *fakeJson = @"{\"result\":{\"result\":\"success\",\"msTime\":1899999999999,\"licenses\":[{\"benefits\":[\"RemoveWatermark\",\"MemberEffects\",\"ProjectPackageSharing\",\"FutureMemberFeatures\",\"AdvancedEasing\",\"CameraObjects\",\"LayerParenting\",\"CloudStorageLowTier\",\"RemoveAds\",\"AdvancedLayerEffects\"],\"type\":\"subscription\",\"store\":\"apple_app_store\",\"autoRenewing\":true,\"orderNumber\":\"300001752007005\",\"productId\":\"alightcreative.motion.1y_t60_1w\",\"period\":\"1y\",\"valid\":true,\"linkStatus\":\"linked-current\"}],\"warnings\":[]}}";
    NSData *finalData = [fakeJson dataUsingEncoding:NSUTF8StringEncoding];
    [self.client URLProtocol:self didReceiveResponse:self.response cacheStoragePolicy:NSURLCacheStorageNotAllowed];
    [self.client URLProtocol:self didLoadData:finalData];
    [self.client URLProtocolDidFinishLoading:self];
}

@end

#pragma mark - 2. NSURLSession swizzle — inject AMProxyProtocol
static id (*orig_sessionWithConfig)(id, SEL, NSURLSessionConfiguration *, id, NSOperationQueue *);
static id swizzled_sessionWithConfig(id self, SEL _cmd, NSURLSessionConfiguration *config, id delegate, NSOperationQueue *queue) {
    if (config) {
        NSMutableArray *protocols = [config.protocolClasses mutableCopy] ?: [NSMutableArray array];
        if (![protocols containsObject:[AMProxyProtocol class]]) {
            [protocols insertObject:[AMProxyProtocol class] atIndex:0];
        }
        config.protocolClasses = protocols;
    }
    return orig_sessionWithConfig(self, _cmd, config, delegate, queue);
}

#pragma mark - 3. StoreKit hooks — inject product ID, block invalid IDs
static id (*orig_initWithProductIdentifiers)(id, SEL, NSSet *);
static id swizzled_initWithProductIdentifiers(id self, SEL _cmd, NSSet *productIdentifiers) {
    productIdentifiers = [NSSet setWithArray:@[@"alightcreative.motion.1y_t60_1w", @"alightcreative.motion.1y_", @"alightcreative.motion.1m_", @"alightcreative.motion.1w_"]];
    return orig_initWithProductIdentifiers(self, _cmd, productIdentifiers);
}

static id (*orig_invalidProductIdentifiers)(id, SEL);
static id swizzled_invalidProductIdentifiers(id self, SEL _cmd) { return @[]; }

#pragma mark - 4. UIAlertController anti-crash
static id (*orig_presentViewController)(id, SEL, id, BOOL, id);
static void swizzled_presentViewController(id self, SEL _cmd, id viewControllerToPresent, BOOL flag, id completion) {
    if ([viewControllerToPresent isKindOfClass:[UIAlertController class]]) {
        UIAlertController *alert = (UIAlertController *)viewControllerToPresent;
        NSString *title = alert.title.lowercaseString;
        NSString *msg = alert.message.lowercaseString;
        if ([title containsString:@"21008"] || [title containsString:@"21009"] ||
            [msg containsString:@"21008"] || [msg containsString:@"21009"] ||
            [msg containsString:@"product list empty"] || [msg containsString:@"empty"] ||
            [msg containsString:@"cannot connect"] || [msg containsString:@"storekit"]) {
            NSLog(@"[AMPrem] Blocked alert: %@ - %@", title, msg);
            return;
        }
    }
    orig_presentViewController(self, _cmd, viewControllerToPresent, flag, completion);
}

#pragma mark - 5. NSUserDefaults + Remote Config injection
static id (*orig_standardUserDefaults)(id, SEL);
static id swizzled_standardUserDefaults(id self, SEL _cmd) {
    id defaults = orig_standardUserDefaults(self, _cmd);
    static dispatch_once_t once;
    dispatch_once(&once, ^{
        @try {
            // Force fallback to legacy IAPManager pipeline
            [defaults setBool:YES forKey:@"is_fallback_on_bspmonetization_enabled"];
            [defaults setBool:YES forKey:@"fallback_on_bspmonetization"];
            // Disable Oracle/EntitlementsRefresher
            [defaults setBool:NO forKey:@"is_fallback_on_bspmonetization_enabled"];
            [defaults setBool:YES forKey:@"fallback_on_bspmonetization"];
            // Force premium state directly
            [defaults setBool:YES forKey:@"is_premium"];
            [defaults setBool:YES forKey:@"premium_user"];
            [defaults setBool:YES forKey:@"hasActiveSubscription"];
            [defaults synchronize];
        } @catch (NSException *e) {
            NSLog(@"[AMPrem] NSUserDefaults injection error: %@", e);
        }
    });
    return defaults;
}

static void patchIAPManagerInstance(void) {
    // REMOVED: Direct memory patching via hardcoded offsets (+0x39 / +0x3A)
    // was causing EXC_BAD_ACCESS crashes due to struct layout changes in newer versions.
    // The boolean hooks in patchBSPStateManager and globalPremiumHook are sufficient.
    NSLog(@"[AMPrem] patchIAPManagerInstance bypassed (unsafe memory offset patch removed).");
}

#pragma mark - 7. BSP Monetization StateManager hooks
static void patchBSPStateManager(void) {
    Class stateMgr = objc_getClass("_TtCE29BSPMonetizationImplementationV15BSPMonetization15BSPMonetization12StateManager");
    if (!stateMgr) {
        // Try to find any StateManager class
        int numClasses = objc_getClassList(NULL, 0);
        if (numClasses <= 0) return;
        Class *classes = (Class *)malloc(sizeof(Class) * numClasses);
        objc_getClassList(classes, numClasses);
        for (int i = 0; i < numClasses; i++) {
            const char *name = class_getName(classes[i]);
            if (strstr(name, "StateManager") != NULL || strstr(name, "EntitlementsRefresher") != NULL) {
                stateMgr = classes[i];
                NSLog(@"[AMPrem] Found state class: %s", name);
            }
        }
        free(classes);
    }
    if (!stateMgr) return;

    // Patch StateManager premium-related selectors
    NSArray *premiumSels = @[
        @"isPremium", @"isPremiumUser", @"isSubscribed", @"hasActiveSubscription",
        @"isSubscriptionActive", @"hasPremium", @"isSubscriber",
    ];
    for (NSString *selName in premiumSels) {
        patchSelectorOnClass(stateMgr, selName, (IMP)returnYes);
    }
}

#pragma mark - 8. Additional targeted hooks for ReceiptClient / EntitlementsRefresher
static void patchReceiptAndEntitlements(void) {
    // EntitlementsRefresher hooks
    Class refreshClasses[] = {
        objc_getClass("EntitlementsRefresher"),
        objc_getClass("ReceiptClient"),
        objc_getClass("ReceiptClientV2"),
        objc_getClass("OracleSubscription"),
        objc_getClass("LicenseStore"),
        objc_getClass("ProductLicense"),
    };
    for (int i = 0; i < 6; i++) {
        Class cls = refreshClasses[i];
        if (!cls) continue;
        patchSelectorOnClass(cls, @"isPremium", (IMP)returnYes);
        patchSelectorOnClass(cls, @"isPremiumUser", (IMP)returnYes);
        patchSelectorOnClass(cls, @"isSubscribed", (IMP)returnYes);
        patchSelectorOnClass(cls, @"hasActiveSubscription", (IMP)returnYes);
        patchSelectorOnClass(cls, @"purchaseExpired", (IMP)returnNo);
        patchSelectorOnClass(cls, @"oracleVerificationPending", (IMP)returnNo);
    }
}

#pragma mark - 9. Global scan: patch all premium BOOL selectors
static void globalPremiumHook(void) {
    NSArray *targetTrue = @[
        @"isPremiumUser", @"hasPremium", @"isPremium", @"isSubscribed",
        @"hasActiveSubscription", @"isSubscriptionActive", @"isSubscriber",
        @"isProUser", @"unlockedPremiumUser",
    ];
    NSArray *targetFalse = @[
        @"isFreeUser", @"isSpooner", @"subscriptionRequired",
        @"purchaseExpired", @"oracleVerificationPending",
    ];

    unsigned int imageCount = 0;
    const char **imageNames = objc_copyImageNames(&imageCount);
    if (!imageNames) return;

    for (int i = 0; i < imageCount; i++) {
        const char *imageName = imageNames[i];
        // Only scan app and its frameworks to prevent initializing unrelated classes or crashing
        if (strstr(imageName, "Alight") || strstr(imageName, "BSP") || strstr(imageName, "Monetization")) {
            unsigned int classCount = 0;
            const char **classNames = objc_copyClassNamesForImage(imageName, &classCount);
            if (classNames) {
                for (int j = 0; j < classCount; j++) {
                    Class cls = objc_getClass(classNames[j]);
                    if (!cls) continue;

                    for (NSString *selName in targetTrue) {
                        patchSelectorOnClass(cls, selName, (IMP)returnYes);
                    }
                    for (NSString *selName in targetFalse) {
                        patchSelectorOnClass(cls, selName, (IMP)returnNo);
                    }
                }
                free(classNames);
            }
        }
    }
    free(imageNames);
}

#pragma mark - Constructor
__attribute__((constructor))
static void init() {
    NSLog(@"[AMPrem] Loaded — waiting for app launch");
}

@interface AMPremLoader : NSObject
@end

@implementation AMPremLoader
+ (void)load {
    NSLog(@"[AMPrem] +load called, starting background poll for LiveContainer compat...");
    
    // In LiveContainer, the guest app classes might be loaded dynamically after the tweak.
    // UIApplicationDidFinishLaunchingNotification might be missed or fired by the host app.
    // We poll for the guest app's classes in the background.
    dispatch_async(dispatch_get_global_queue(DISPATCH_QUEUE_PRIORITY_DEFAULT, 0), ^{
        Class targetClass = Nil;
        int retries = 0;
        
        while (!targetClass && retries < 100) { // Poll for up to 50 seconds
            targetClass = objc_getClass("AlightMotion.IAPManager");
            if (!targetClass) targetClass = objc_getClass("_TtC12AlightMotion10IAPManager");
            if (!targetClass) targetClass = objc_getClass("EntitlementsRefresher");
            
            if (!targetClass) {
                [NSThread sleepForTimeInterval:0.5];
                retries++;
            }
        }
        
        if (targetClass) {
            NSLog(@"[AMPrem] Guest app classes loaded! Applying patches on main thread...");
            dispatch_async(dispatch_get_main_queue(), ^{
                [self applyPatches];
            });
        } else {
            NSLog(@"[AMPrem] Timeout waiting for guest app classes.");
        }
    });
}

+ (void)applyPatches {
    NSLog(@"[AMPrem] Applying premium patches");

    // ---- Stage 1: NSUserDefaults injection ----
    Method defaultsMethod = class_getClassMethod([NSUserDefaults class], @selector(standardUserDefaults));
    if (defaultsMethod) {
        orig_standardUserDefaults = (__typeof(orig_standardUserDefaults))method_getImplementation(defaultsMethod);
        method_setImplementation(defaultsMethod, (IMP)swizzled_standardUserDefaults);
    }

    // ---- Stage 2: Oracle interception via NSURLProtocol ----
    [NSURLProtocol registerClass:[AMProxyProtocol class]];

    // ---- Stage 3: NSURLSessionConfig injection ----
    Class sessionClass = objc_getClass("NSURLSession");
    if (sessionClass) {
        Method m = class_getClassMethod(sessionClass, @selector(sessionWithConfiguration:delegate:delegateQueue:));
        if (m) {
            orig_sessionWithConfig = (__typeof(orig_sessionWithConfig))method_getImplementation(m);
            method_setImplementation(m, (IMP)swizzled_sessionWithConfig);
        }
    }

    // ---- Stage 4: StoreKit hooks ----
    Class skpr = objc_getClass("SKProductsRequest");
    if (skpr) {
        Method m = class_getInstanceMethod(skpr, @selector(initWithProductIdentifiers:));
        if (m) {
            orig_initWithProductIdentifiers = (__typeof(orig_initWithProductIdentifiers))method_getImplementation(m);
            method_setImplementation(m, (IMP)swizzled_initWithProductIdentifiers);
        }
    }
    Class skpresp = objc_getClass("SKProductsResponse");
    if (skpresp) {
        Method m = class_getInstanceMethod(skpresp, @selector(invalidProductIdentifiers));
        if (m) {
            orig_invalidProductIdentifiers = (__typeof(orig_invalidProductIdentifiers))method_getImplementation(m);
            method_setImplementation(m, (IMP)swizzled_invalidProductIdentifiers);
        }
    }
    Class skpay = objc_getClass("SKPaymentQueue");
    if (skpay) {
        patchSelectorOnClass(skpay, @"isStoreKit2Available", (IMP)returnNo);
    }

    // ---- Stage 5: Anti-crash alert blocker ----
    Class vc = objc_getClass("UIViewController");
    if (vc) {
        Method m = class_getInstanceMethod(vc, @selector(presentViewController:animated:completion:));
        if (m) {
            orig_presentViewController = (__typeof(orig_presentViewController))method_getImplementation(m);
            method_setImplementation(m, (IMP)swizzled_presentViewController);
        }
    }

    // ---- Stage 6: InAppReceipt hooks ----
    Class iap = objc_getClass("InAppReceipt");
    if (iap) {
        for (NSString *selName in @[@"isValid", @"verify", @"verifyHash", @"verifySignature"]) {
            Method m = class_getInstanceMethod(iap, NSSelectorFromString(selName));
            if (m) method_setImplementation(m, (IMP)returnYes);
        }
    }

    // ---- Stage 7: Immediate IAPManager memory patch ----
    patchIAPManagerInstance();

    // ---- Stage 8: BSP Monetization hooks ----
    patchBSPStateManager();

    // ---- Stage 9: Receipt/Entitlements hooks ----
    patchReceiptAndEntitlements();

    // ---- Stage 10: Delayed global scan (after all classes load) ----
    dispatch_async(dispatch_get_main_queue(), ^{
        globalPremiumHook();

        // Retry IAPManager patch after full init
        patchIAPManagerInstance();

        // Periodic refresh of IAPManager field (some classes may recreate it)
        dispatch_async(dispatch_get_global_queue(DISPATCH_QUEUE_PRIORITY_BACKGROUND, 0), ^{
            [NSThread sleepForTimeInterval:3.0];
            patchIAPManagerInstance();
            [NSThread sleepForTimeInterval:10.0];
            patchIAPManagerInstance();
        });

        NSLog(@"[AMPrem] All premium patches applied");
    });
}

@end
