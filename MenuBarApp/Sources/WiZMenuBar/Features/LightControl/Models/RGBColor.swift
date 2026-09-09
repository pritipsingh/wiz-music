import AppKit
import SwiftUI

struct RGBColor: Equatable, Sendable {
    let red: Int
    let green: Int
    let blue: Int

    init(red: Int, green: Int, blue: Int) {
        self.red = min(255, max(0, red))
        self.green = min(255, max(0, green))
        self.blue = min(255, max(0, blue))
    }

    init(red: Double, green: Double, blue: Double) {
        self.init(
            red: Int(red.rounded()),
            green: Int(green.rounded()),
            blue: Int(blue.rounded())
        )
    }

    init(color: Color) {
        let converted = NSColor(color).usingColorSpace(.deviceRGB)
        self.init(
            red: Int((converted?.redComponent ?? 1) * 255),
            green: Int((converted?.greenComponent ?? 1) * 255),
            blue: Int((converted?.blueComponent ?? 1) * 255)
        )
    }

    var color: Color {
        Color(
            red: Double(red) / 255,
            green: Double(green) / 255,
            blue: Double(blue) / 255
        )
    }
}

struct LightPreset: Identifiable, Equatable {
    let name: String
    let color: RGBColor

    var id: String { name }

    static let all: [LightPreset] = [
        LightPreset(
            name: "Warm",
            color: RGBColor(red: 255, green: 147, blue: 72)
        ),
        LightPreset(
            name: "Sunset",
            color: RGBColor(red: 255, green: 72, blue: 92)
        ),
        LightPreset(
            name: "Ocean",
            color: RGBColor(red: 40, green: 132, blue: 255)
        ),
        LightPreset(
            name: "Mint",
            color: RGBColor(red: 66, green: 220, blue: 166)
        ),
        LightPreset(
            name: "Violet",
            color: RGBColor(red: 153, green: 92, blue: 255)
        ),
    ]
}
