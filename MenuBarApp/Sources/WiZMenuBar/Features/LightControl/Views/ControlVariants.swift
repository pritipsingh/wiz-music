import SwiftUI

struct QuickControlsView: View {
    @Binding var color: Color
    @Binding var brightness: Double
    let apply: () -> Void
    let selectPreset: (LightPreset) -> Void

    var body: some View {
        VStack(spacing: 16) {
            ColorPicker("Color", selection: $color, supportsOpacity: false)
                .font(.headline)
            BrightnessSlider(brightness: $brightness)
            PresetStrip(selectPreset: selectPreset)
            ApplyButton(action: apply)
        }
    }
}

struct PaletteControlsView: View {
    let selectedColor: RGBColor
    @Binding var color: Color
    @Binding var brightness: Double
    let apply: () -> Void
    let selectPreset: (LightPreset) -> Void

    var body: some View {
        VStack(alignment: .leading, spacing: 16) {
            Text("Choose a mood")
                .font(.headline)
            HStack(spacing: 8) {
                ForEach(LightPreset.all) { preset in
                    PresetSwatchButton(
                        preset: preset,
                        isSelected: preset.color == selectedColor,
                        action: { selectPreset(preset) }
                    )
                }
            }
            HStack {
                ColorPicker(
                    "Custom color",
                    selection: $color,
                    supportsOpacity: false
                )
                Button("Apply") {
                    apply()
                }
                .buttonStyle(.bordered)
            }
            BrightnessSlider(brightness: $brightness)
        }
    }
}

struct StudioControlsView: View {
    @Binding var red: Double
    @Binding var green: Double
    @Binding var blue: Double
    @Binding var brightness: Double
    let apply: () -> Void

    var body: some View {
        VStack(spacing: 10) {
            RGBSlider(label: "R", value: $red, tint: .red)
            RGBSlider(label: "G", value: $green, tint: .green)
            RGBSlider(label: "B", value: $blue, tint: .blue)
            BrightnessSlider(brightness: $brightness)
            ApplyButton(action: apply)
        }
    }
}

private struct BrightnessSlider: View {
    @Binding var brightness: Double

    var body: some View {
        HStack(spacing: 8) {
            Image(systemName: "sun.min")
                .accessibilityHidden(true)
            Slider(value: $brightness, in: 10...100, step: 1)
                .accessibilityLabel("Brightness")
            Text("\(Int(brightness))%")
                .font(.caption.monospacedDigit())
                .foregroundStyle(.secondary)
                .frame(width: 36, alignment: .trailing)
        }
    }
}

private struct RGBSlider: View {
    let label: String
    @Binding var value: Double
    let tint: Color

    var body: some View {
        HStack(spacing: 8) {
            Text(label)
                .font(.caption.monospaced())
                .frame(width: 16)
            Slider(value: $value, in: 0...255, step: 1)
                .tint(tint)
                .accessibilityLabel("\(label) color value")
            Text("\(Int(value))")
                .font(.caption.monospacedDigit())
                .foregroundStyle(.secondary)
                .frame(width: 28, alignment: .trailing)
        }
    }
}

private struct PresetStrip: View {
    let selectPreset: (LightPreset) -> Void

    var body: some View {
        HStack(spacing: 8) {
            ForEach(LightPreset.all) { preset in
                Button {
                    selectPreset(preset)
                } label: {
                    Circle()
                        .fill(preset.color.color.gradient)
                        .frame(width: 32, height: 32)
                        .overlay {
                            Circle().strokeBorder(.white.opacity(0.35))
                        }
                        .frame(width: 40, height: 40)
                }
                .buttonStyle(.plain)
                .help(preset.name)
                .accessibilityLabel("Set \(preset.name) color")
            }
        }
    }
}

private struct PresetSwatchButton: View {
    let preset: LightPreset
    let isSelected: Bool
    let action: () -> Void

    var body: some View {
        Button(action: action) {
            ZStack {
                RoundedRectangle(cornerRadius: 10)
                    .fill(preset.color.color.gradient)
                if isSelected {
                    Image(systemName: "checkmark")
                        .font(.system(size: 14, weight: .bold))
                        .foregroundStyle(.white)
                        .shadow(radius: 1)
                }
            }
            .frame(width: 48, height: 48)
            .overlay {
                RoundedRectangle(cornerRadius: 10)
                    .strokeBorder(.white.opacity(0.3))
            }
        }
        .buttonStyle(.plain)
        .help(preset.name)
        .accessibilityLabel("Set \(preset.name) color")
        .accessibilityValue(isSelected ? "Selected" : "Not selected")
    }
}

private struct ApplyButton: View {
    let action: () -> Void

    var body: some View {
        Button("Apply color", action: action)
            .buttonStyle(.borderedProminent)
            .controlSize(.large)
            .frame(maxWidth: .infinity)
    }
}
