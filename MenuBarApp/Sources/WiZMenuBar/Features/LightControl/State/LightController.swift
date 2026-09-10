import SwiftUI

@MainActor
final class LightController: ObservableObject {
    enum Status: Equatable {
        case idle
        case sending
        case success(String)
        case error(String)

        var message: String {
            switch self {
            case .idle:
                "Ready"
            case .sending:
                "Sending to bulb..."
            case let .success(message), let .error(message):
                message
            }
        }

        var symbol: String {
            switch self {
            case .idle:
                "circle"
            case .sending:
                "arrow.triangle.2.circlepath"
            case .success:
                "checkmark.circle.fill"
            case .error:
                "exclamationmark.triangle.fill"
            }
        }

        var color: Color {
            switch self {
            case .idle:
                .secondary
            case .sending:
                .accentColor
            case .success:
                .green
            case .error:
                .red
            }
        }
    }

    @Published private(set) var status: Status = .idle
    @Published private(set) var isOn = true

    private let client = WiZClient()
    private var clearStatusTask: Task<Void, Never>?

    func apply(color: RGBColor, brightness: Int, address: String) {
        guard validate(address) else { return }
        perform(success: "Color applied") { [client] in
            try await client.setColor(
                color,
                brightness: brightness,
                at: address
            )
            return true
        }
    }

    func setPower(
        _ shouldTurnOn: Bool,
        color: RGBColor,
        brightness: Int,
        address: String
    ) {
        guard validate(address) else { return }
        perform(success: shouldTurnOn ? "Light turned on" : "Light turned off") {
            [client] in
            if shouldTurnOn {
                try await client.setColor(
                    color,
                    brightness: brightness,
                    at: address
                )
            } else {
                try await client.turnOff(at: address)
            }
            return shouldTurnOn
        }
    }

    private func validate(_ address: String) -> Bool {
        guard WiZClient.isValidIPv4(address) else {
            status = .error("Enter a valid bulb address")
            return false
        }
        return true
    }

    private func perform(
        success message: String,
        operation: @escaping @Sendable () async throws -> Bool
    ) {
        clearStatusTask?.cancel()
        status = .sending

        Task {
            do {
                let powerState = try await operation()
                isOn = powerState
                status = .success(message)
                scheduleStatusReset()
            } catch {
                status = .error(
                    (error as? LocalizedError)?.errorDescription
                        ?? "Could not reach the bulb."
                )
            }
        }
    }

    private func scheduleStatusReset() {
        clearStatusTask = Task {
            try? await Task.sleep(for: .seconds(2))
            guard !Task.isCancelled else { return }
            status = .idle
        }
    }
}
