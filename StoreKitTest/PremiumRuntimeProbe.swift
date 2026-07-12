import Foundation
import StoreKit

/// Reports only verified StoreKit entitlements in an authorized development app.
/// It does not infer Premium from UI flags, dylibs, strings, or local JSON.
public enum PremiumRuntimeProbe {
    public struct Result: Sendable {
        public let productID: String
        public let isVerified: Bool
        public let isActive: Bool
        public let expirationDate: Date?
    }

    public static func currentEntitlement(for productID: String) async -> Result {
        for await item in Transaction.currentEntitlements {
            guard case .verified(let transaction) = item,
                  transaction.productID == productID else { continue }
            let active = transaction.revocationDate == nil &&
                (transaction.expirationDate.map { $0 > Date() } ?? true)
            return Result(productID: productID, isVerified: true,
                          isActive: active,
                          expirationDate: transaction.expirationDate)
        }
        return Result(productID: productID, isVerified: false,
                      isActive: false, expirationDate: nil)
    }
}
