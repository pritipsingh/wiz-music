import SwiftUI

@main
struct WiZMenuBarApp: App {
    @NSApplicationDelegateAdaptor(AppDelegate.self) private var appDelegate

    var body: some Scene {
        MenuBarExtra("WiZ Light", systemImage: "lightbulb.fill") {
            ControlPopoverView()
        }
        .menuBarExtraStyle(.window)
    }
}

final class AppDelegate: NSObject, NSApplicationDelegate {
    private var previewWindow: NSWindow?

    func applicationDidFinishLaunching(_ notification: Notification) {
        guard ProcessInfo.processInfo.environment["WIZ_PREVIEW"] == "1" else {
            return
        }

        let window = NSWindow(
            contentRect: NSRect(x: 0, y: 0, width: 328, height: 384),
            styleMask: [.titled, .closable],
            backing: .buffered,
            defer: false
        )
        window.title = "WiZ Light Preview"
        window.contentView = NSHostingView(rootView: ControlPopoverView())
        window.center()
        window.makeKeyAndOrderFront(nil)
        NSApplication.shared.setActivationPolicy(.regular)
        NSApplication.shared.activate(ignoringOtherApps: true)
        previewWindow = window
    }
}
