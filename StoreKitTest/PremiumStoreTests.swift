import XCTest
import StoreKit
import StoreKitTest

@MainActor
final class PremiumStoreTests: XCTestCase {
    private static let productID = "alightcreative.motion.1y_t60_1w"
    private var session: SKTestSession!

    override func setUpWithError() throws {
        try super.setUpWithError()
        session = try SKTestSession(configurationFileNamed: "PremiumTest")
        session.disableDialogs = true
        session.clearTransactions()
        session.resetToDefaultState()
    }

    override func tearDownWithError() throws {
        session.clearTransactions()
        session = nil
        try super.tearDownWithError()
    }

    func testProductLoadsFromLocalConfiguration() async throws {
        let products = try await Product.products(for: [Self.productID])
        XCTAssertEqual(products.count, 1)
        XCTAssertEqual(products.first?.id, Self.productID)
        XCTAssertEqual(products.first?.type, .autoRenewable)
    }

    func testPurchaseCreatesVerifiedEntitlement() async throws {
        try session.buyProduct(identifier: Self.productID)

        var found = false
        for await result in Transaction.currentEntitlements {
            guard case .verified(let transaction) = result else { continue }
            if transaction.productID == Self.productID,
               transaction.revocationDate == nil,
               transaction.expirationDate.map({ $0 > Date() }) ?? false {
                found = true
                break
            }
        }
        XCTAssertTrue(found, "Expected an active verified Premium entitlement")
    }

    func testExpiredSubscriptionIsNotActive() async throws {
        try session.buyProduct(identifier: Self.productID)
        try session.expireSubscription(productIdentifier: Self.productID)

        var active = false
        for await result in Transaction.currentEntitlements {
            guard case .verified(let transaction) = result else { continue }
            if transaction.productID == Self.productID,
               transaction.revocationDate == nil,
               transaction.expirationDate.map({ $0 > Date() }) ?? false {
                active = true
                break
            }
        }
        XCTAssertFalse(active)
    }
}
