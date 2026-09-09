#!/bin/zsh

set -euo pipefail

repo_dir="$(cd "$(dirname "$0")" && pwd)"
package_dir="$repo_dir/MenuBarApp"
app_dir="$repo_dir/dist/WiZ Light.app"

swift build --package-path "$package_dir" -c release

rm -rf "$app_dir"
mkdir -p "$app_dir/Contents/MacOS"
cp "$package_dir/.build/release/WiZMenuBar" \
    "$app_dir/Contents/MacOS/WiZMenuBar"
cp "$package_dir/Resources/Info.plist" "$app_dir/Contents/Info.plist"

codesign --force --deep --sign - "$app_dir"
echo "$app_dir"
