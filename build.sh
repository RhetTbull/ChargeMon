#!/bin/sh

# Build, sign and package ChargeMon as a DMG file for release
# this requires create-dmg: `brew install create-dmg` to install

#   --background "installer_background.png" \

# build with py2app
echo "Running py2app"
test -d dist && rm -rf dist/
test -d build && rm -rf build/
python setup.py py2app

# sign with adhoc certificate
echo "Signing with codesign"
codesign --force --deep -s - dist/ChargeMon.app

# create installer DMG
echo "Creating DMG"
test -f ChargeMon-Installer.dmg && rm ChargeMon-Installer.dmg
create-dmg \
  --volname "ChargeMon Installer" \
  --volicon "icon.icns" \
  --window-pos 200 120 \
  --window-size 800 400 \
  --icon-size 100 \
  --icon "ChargeMon.app" 200 190 \
  --hide-extension "ChargeMon.app" \
  --app-drop-link 600 185 \
  "ChargeMon-Installer.dmg" \
  "dist/"
