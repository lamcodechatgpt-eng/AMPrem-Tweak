import Foundation

/// Development-only entitlement seam.
///
/// Add this file only to a development/test target. The entire implementation
/// is removed by the compiler for Release builds.
#if DEBUG
public protocol PremiumEntitlementProviding {
    var isPremium: Bool { get }
    var benefits: Set<String> { get }
}

public struct DebugPremiumEntitlement: PremiumEntitlementProviding {
    public let isPremium: Bool
    public let benefits: Set<String>

    public init(isPremium: Bool = true,
                benefits: Set<String> = [
                    "RemoveWatermark",
                    "MemberEffects",
                    "AdvancedEasing",
                    "CameraObjects",
                    "LayerParenting"
                ]) {
        self.isPremium = isPremium
        self.benefits = benefits
    }
}

public enum PremiumEntitlementFactory {
    /// Returns the mock only when both DEBUG and the explicit launch flag are
    /// present. This prevents accidental activation in ordinary debug runs.
    public static func makeProductionSafe(default fallback: PremiumEntitlementProviding) -> PremiumEntitlementProviding {
        guard ProcessInfo.processInfo.environment["DEBUG_PREMIUM_MOCK"] == "1" else {
            return fallback
        }
        return DebugPremiumEntitlement()
    }
}
#endif
