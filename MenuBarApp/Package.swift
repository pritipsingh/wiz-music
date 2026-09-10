// swift-tools-version: 6.0

import PackageDescription

let package = Package(
    name: "WiZMenuBar",
    platforms: [.macOS(.v13)],
    products: [
        .executable(name: "WiZMenuBar", targets: ["WiZMenuBar"]),
    ],
    targets: [
        .executableTarget(name: "WiZMenuBar"),
        .testTarget(
            name: "WiZMenuBarTests",
            dependencies: ["WiZMenuBar"]
        ),
    ]
)
