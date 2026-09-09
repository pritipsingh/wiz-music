import Foundation
import Testing
@testable import WiZMenuBar

struct WiZPayloadTests {
    @Test
    func colorPayloadUsesWiZProtocolAndClampsBrightness() throws {
        let data = try WiZPayloadBuilder.color(
            RGBColor(red: 20, green: 40, blue: 60),
            brightness: 120
        )
        let json = try #require(
            JSONSerialization.jsonObject(with: data) as? [String: Any]
        )
        let params = try #require(json["params"] as? [String: Any])

        #expect(json["method"] as? String == "setPilot")
        #expect(params["r"] as? Int == 20)
        #expect(params["g"] as? Int == 40)
        #expect(params["b"] as? Int == 60)
        #expect(params["dimming"] as? Int == 100)
        #expect(params["state"] as? Bool == true)
    }

    @Test
    func validatesIPv4Addresses() {
        #expect(WiZClient.isValidIPv4("192.168.1.6"))
        #expect(!WiZClient.isValidIPv4(""))
        #expect(!WiZClient.isValidIPv4("192.168.1.999"))
    }

    @Test(
        "Live bulb accepts a native UDP command",
        .enabled(if: ProcessInfo.processInfo.environment["WIZ_BULB_IP"] != nil)
    )
    func liveBulbAcceptsColorCommand() async throws {
        let address = try #require(
            ProcessInfo.processInfo.environment["WIZ_BULB_IP"]
        )
        let client = WiZClient()

        try await client.setColor(
            RGBColor(red: 255, green: 147, blue: 72),
            brightness: 100,
            at: address
        )
    }
}
