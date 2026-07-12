// AlightMotion Premium Unlocker - MITM script for Surge/Quantumult X
// Intercepts cloud function responses and returns premium data
// Product IDs: alightcreative.motion.1y_, alightcreative.motion.1m_, alightcreative.motion.1w_

const premiumResponse = {
  "result": {
    "status": "ready",
    "activeBenefits": [
      "removeWatermark",
      "memberEffects",
      "projectPackageSharing",
      "futureMemberFeatures",
      "advancedEasing",
      "cameraObjects",
      "layerParenting",
      "cloudStorageLowTier",
      "removeAds",
      "advancedLayerEffects"
    ],
    "activeSubscription": {
      "productId": "alightcreative.motion.1y_",
      "periodicity": "year",
      "store": "appleStore",
      "expirationDate": "2099-12-31T23:59:59Z",
      "purchaseDate": "2024-01-01T00:00:00Z",
      "isActive": true
    },
    "activeProducts": ["alightcreative.motion.1y_", "alightcreative.motion.1m_", "alightcreative.motion.1w_"],
    "activeSubscriptionsIDs": ["alightcreative.motion.1y_"],
    "activeLicenses": ["RemoveWatermark", "MemberEffects", "ProjectPackageSharing", "FutureMemberFeatures", "AdvancedEasing", "CameraObjects", "LayerParenting", "CloudStorageLowTier", "RemoveAds", "AdvancedLayerEffects"],
    "isPremium": true,
    "appleAppStoreReceipt": "MIITGQYJKoZIhvcNAQcCoIITCjCCEwYCAQExCzAJBgUrDgMCGgUAMII"
  }
};

const purchaseResponse = {
  "result": {
    "status": "ok",
    "orderNumber": "MOCK-ORDER-12345",
    "productId": "alightcreative.motion.1y_",
    "store": "appleStore",
    "transactionId": "MOCK-TRANSACTION-12345",
    "purchaseDate": "2024-01-01T00:00:00Z",
    "verified": true
  }
};

if (typeof $response !== 'undefined' && $response.body) {
  var url = $request.url || '';
  if (url.indexOf('getAccountStatusAndLicenses') !== -1) {
    $done({ body: JSON.stringify(premiumResponse) });
  } else if (url.indexOf('registerAppStorePurchase') !== -1 || url.indexOf('registerPurchase') !== -1) {
    $done({ body: JSON.stringify(purchaseResponse) });
  } else {
    $done({});
  }
} else {
  $done({});
}
