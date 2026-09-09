import AppKit
import SwiftUI

struct ControlPopoverView: View {
    enum Layout: String, CaseIterable, Identifiable {
        case quick
        case palette
        case studio

        var id: Self { self }

        var label: String {
            rawValue.capitalized
        }
    }

    @AppStorage("bulbAddress") private var bulbAddress = "192.168.1.6"
    @AppStorage("brightness") private var brightness = 100.0
    @AppStorage("red") private var red = 255.0
    @AppStorage("green") private var green = 147.0
    @AppStorage("blue") private var blue = 72.0
    @AppStorage("layout") private var layout = Layout.quick
    @StateObject private var controller = LightController()

    private var rgbColor: RGBColor {
        RGBColor(red: red, green: green, blue: blue)
    }

    private var colorBinding: Binding<Color> {
        Binding(
            get: { rgbColor.color },
            set: { newColor in
                let converted = RGBColor(color: newColor)
                red = Double(converted.red)
                green = Double(converted.green)
                blue = Double(converted.blue)
            }
        )
    }

    var body: some View {
        VStack(spacing: 16) {
            header
            layoutPicker

            Group {
                switch layout {
                case .quick:
                    QuickControlsView(
                        color: colorBinding,
                        brightness: $brightness,
                        apply: apply,
                        selectPreset: selectPreset
                    )
                case .palette:
                    PaletteControlsView(
                        selectedColor: rgbColor,
                        color: colorBinding,
                        brightness: $brightness,
                        apply: apply,
                        selectPreset: selectPreset
                    )
                case .studio:
                    StudioControlsView(
                        red: $red,
                        green: $green,
                        blue: $blue,
                        brightness: $brightness,
                        apply: apply
                    )
                }
            }
            .frame(height: 160, alignment: .top)

            Divider()
            addressField
            statusRow
        }
        .padding(16)
        .frame(width: 328, height: 384)
    }

    private var header: some View {
        HStack(spacing: 12) {
            ZStack {
                Circle()
                    .fill(rgbColor.color.gradient)
                Image(systemName: "lightbulb.fill")
                    .font(.system(size: 18, weight: .semibold))
                    .foregroundStyle(.white)
                    .shadow(radius: 1)
            }
            .frame(width: 40, height: 40)
            .accessibilityHidden(true)

            VStack(alignment: .leading, spacing: 2) {
                Text("WiZ Light")
                    .font(.headline)
                Text(controller.isOn ? "Light is on" : "Light is off")
                    .font(.caption)
                    .foregroundStyle(.secondary)
            }

            Spacer()

            Button {
                controller.setPower(
                    !controller.isOn,
                    color: rgbColor,
                    brightness: Int(brightness),
                    address: bulbAddress
                )
            } label: {
                Image(systemName: "power")
                    .frame(width: 24, height: 24)
            }
            .buttonStyle(.borderedProminent)
            .tint(controller.isOn ? .accentColor : .secondary)
            .disabled(controller.status == .sending)
            .help(controller.isOn ? "Turn light off" : "Turn light on")
            .accessibilityLabel(controller.isOn ? "Turn light off" : "Turn light on")
        }
    }

    private var layoutPicker: some View {
        Picker("Layout", selection: $layout) {
            ForEach(Layout.allCases) { option in
                Text(option.label).tag(option)
            }
        }
        .pickerStyle(.segmented)
        .labelsHidden()
    }

    private var addressField: some View {
        HStack(spacing: 8) {
            Image(systemName: "wifi")
                .foregroundStyle(.secondary)
                .accessibilityHidden(true)
            TextField("Bulb IP address", text: $bulbAddress)
                .textFieldStyle(.plain)
                .accessibilityLabel("Bulb IP address")
            Button("Test") {
                apply()
            }
            .controlSize(.small)
            .disabled(controller.status == .sending)
        }
        .padding(.horizontal, 12)
        .frame(height: 40)
        .background(.quaternary, in: RoundedRectangle(cornerRadius: 10))
    }

    private var statusRow: some View {
        HStack(spacing: 8) {
            Image(systemName: controller.status.symbol)
                .foregroundStyle(controller.status.color)
            Text(controller.status.message)
                .font(.caption)
                .foregroundStyle(.secondary)
                .lineLimit(2)
            Spacer()
            Button("Quit") {
                NSApplication.shared.terminate(nil)
            }
            .buttonStyle(.plain)
            .font(.caption)
            .foregroundStyle(.secondary)
        }
        .frame(height: 32)
        .accessibilityElement(children: .combine)
        .accessibilityLabel(controller.status.message)
    }

    private func apply() {
        controller.apply(
            color: rgbColor,
            brightness: Int(brightness),
            address: bulbAddress
        )
    }

    private func selectPreset(_ preset: LightPreset) {
        red = Double(preset.color.red)
        green = Double(preset.color.green)
        blue = Double(preset.color.blue)
        controller.apply(
            color: preset.color,
            brightness: Int(brightness),
            address: bulbAddress
        )
    }
}
