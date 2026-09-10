import Darwin
import Foundation

enum WiZClientError: LocalizedError, Equatable {
    case invalidAddress
    case socketCreation
    case sendFailed
    case noResponse
    case rejected

    var errorDescription: String? {
        switch self {
        case .invalidAddress:
            "Enter a valid IPv4 bulb address."
        case .socketCreation:
            "Could not open a local network connection."
        case .sendFailed:
            "The color command could not be sent."
        case .noResponse:
            "The bulb did not reply. Check Wi-Fi and its address."
        case .rejected:
            "The bulb rejected the command."
        }
    }
}

enum WiZPayloadBuilder {
    static func color(_ color: RGBColor, brightness: Int) throws -> Data {
        try data(params: [
            "state": true,
            "r": color.red,
            "g": color.green,
            "b": color.blue,
            "dimming": min(100, max(10, brightness)),
        ])
    }

    static func powerOff() throws -> Data {
        try data(params: ["state": false])
    }

    private static func data(params: [String: Any]) throws -> Data {
        try JSONSerialization.data(withJSONObject: [
            "method": "setPilot",
            "params": params,
        ])
    }
}

actor WiZClient {
    private let port: UInt16 = 38_899

    func setColor(
        _ color: RGBColor,
        brightness: Int,
        at address: String
    ) throws {
        let payload = try WiZPayloadBuilder.color(
            color,
            brightness: brightness
        )
        try send(payload, to: address)
    }

    func turnOff(at address: String) throws {
        try send(WiZPayloadBuilder.powerOff(), to: address)
    }

    nonisolated static func isValidIPv4(_ address: String) -> Bool {
        var parsed = in_addr()
        return address.withCString {
            inet_pton(AF_INET, $0, &parsed) == 1
        }
    }

    private func send(_ payload: Data, to address: String) throws {
        guard Self.isValidIPv4(address) else {
            throw WiZClientError.invalidAddress
        }

        let descriptor = socket(AF_INET, SOCK_DGRAM, IPPROTO_UDP)
        guard descriptor >= 0 else {
            throw WiZClientError.socketCreation
        }
        defer { close(descriptor) }

        var timeout = timeval(tv_sec: 1, tv_usec: 0)
        setsockopt(
            descriptor,
            SOL_SOCKET,
            SO_RCVTIMEO,
            &timeout,
            socklen_t(MemoryLayout<timeval>.size)
        )

        var destination = sockaddr_in()
        destination.sin_len = UInt8(MemoryLayout<sockaddr_in>.size)
        destination.sin_family = sa_family_t(AF_INET)
        destination.sin_port = port.bigEndian
        address.withCString {
            _ = inet_pton(AF_INET, $0, &destination.sin_addr)
        }

        let sent = withUnsafePointer(to: &destination) { pointer in
            pointer.withMemoryRebound(to: sockaddr.self, capacity: 1) {
                socketAddress in
                payload.withUnsafeBytes { bytes in
                    sendto(
                        descriptor,
                        bytes.baseAddress,
                        bytes.count,
                        0,
                        socketAddress,
                        socklen_t(MemoryLayout<sockaddr_in>.size)
                    )
                }
            }
        }
        guard sent == payload.count else {
            throw WiZClientError.sendFailed
        }

        var response = [UInt8](repeating: 0, count: 1_024)
        let count = recv(descriptor, &response, response.count, 0)
        guard count > 0 else {
            throw WiZClientError.noResponse
        }

        let data = Data(response.prefix(count))
        guard
            let json = try? JSONSerialization.jsonObject(with: data)
                as? [String: Any],
            let result = json["result"] as? [String: Any],
            result["success"] as? Bool == true
        else {
            throw WiZClientError.rejected
        }
    }
}
