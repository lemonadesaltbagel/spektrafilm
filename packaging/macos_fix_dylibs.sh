#!/usr/bin/env bash
# Rename lensfunpy's vendored libintl before running PyInstaller on macOS.
#
# The lensfunpy and exiv2 wheels each vendor a different library named
# libintl.8.dylib (glib's proxy-libintl vs. GNU gettext). PyInstaller resolves
# macOS dependencies by basename, so both packages end up linked against one
# of them and lensfunpy fails to load with
#   Symbol not found: _g_libintl_bind_textdomain_codeset
# Giving lensfunpy's copy a unique name keeps the two apart.
set -euo pipefail

dylibs="$(python -c 'import os, lensfunpy; print(os.path.join(os.path.dirname(lensfunpy.__file__), ".dylibs"))')"
cd "$dylibs"

if [[ ! -f libintl.8.dylib ]]; then
  echo "lensfunpy: no vendored libintl.8.dylib, nothing to do"
  exit 0
fi

mv libintl.8.dylib libglibintl.8.dylib
install_name_tool -id @loader_path/libglibintl.8.dylib libglibintl.8.dylib
for lib in *.dylib; do
  if otool -L "$lib" | grep -q '@loader_path/libintl.8.dylib'; then
    install_name_tool -change @loader_path/libintl.8.dylib @loader_path/libglibintl.8.dylib "$lib"
  fi
done
# install_name_tool invalidates signatures; arm64 refuses to load unsigned code.
for lib in *.dylib; do
  codesign --force --sign - "$lib"
done
echo "lensfunpy: renamed vendored libintl.8.dylib to libglibintl.8.dylib"
