#!/usr/bin/env bash

set -e

INSTALLDIR=${1:-$PWD/BUILD_native_dyn/INSTALL}
SOURCEDIR=${2:-$PWD/SOURCE/kiwix-desktop}
APPDIR=${3:-$PWD/AppDir}

SYSTEMLIBDIR=lib/x86_64-linux-gnu
if [ ! -e "$INSTALLDIR/lib" ] ; then
  SYSTEMLIBDIR=lib64
fi

ICONFILE=$SOURCEDIR/resources/icons/kiwix/scalable/kiwix-desktop.svg
DESKTOPFILE=$SOURCEDIR/resources/org.kiwix.desktop.desktop

# Create structure
mkdir -p $APPDIR/usr/{bin,lib,share} $APPDIR/usr/share/applications $APPDIR/usr/share/icons/hicolor/48x48/apps
# Copy our files
cp $INSTALLDIR/bin/kiwix-desktop $APPDIR/usr/bin/
cp $INSTALLDIR/$SYSTEMLIBDIR/*.so* $APPDIR/usr/lib
# Remove it as it break with linuxdeployqt (should we compile without it) ?
rm -f $APPDIR/usr/lib/libmagic.so*
# Copy nss lib (to not conflict with host's ones)
cp -a /usr/$SYSTEMLIBDIR/nss $APPDIR/usr/lib
# Copy libthai.so (see kiwix-desktop issue#1016)
cp -a /usr/$SYSTEMLIBDIR/libthai.so* $APPDIR/usr/lib

# Copy ssl libs so that the appimage runs on newer systems
# that use a backward incompatible version of openssl
cp /usr/$SYSTEMLIBDIR/lib{crypto,ssl}.so.1.1 $APPDIR/usr/lib

patch_rodata()
{
    local elffile=$1
    local sedscript=$2
    local rodatafile=$elffile.rodata
    objcopy --dump-section .rodata="$rodatafile" "$elffile"
    sed -i "$sedscript" "$rodatafile"
    objcopy --update-section .rodata="$rodatafile" "$elffile"
    rm $rodatafile
}

# copy and patch a couple of libs depending on ssl functionalty before
# linuxdeployqt copies and modifies them whereupon the patch_rodata procedure
# stops working on them correctly
cp -rL /usr/$SYSTEMLIBDIR/{libgnutls.so.30,libQt5Network.so.5} $APPDIR/usr/lib

# patch libQt5Network.so so that if it fails to load certificates from
# system paths the last path that it tries points to the certificate bundle
# included with the appimage

# !!! crt_bundle_new_path must have the same length as crt_bundle_old_path
crt_bundle_old_path=/usr/local/share/certs/ca-root-nss.crt
crt_bundle_new_path=/tmp/cert_bundle_provided_by_kiwix.crt
# !!! crt_bundle_new_path must have the same length as crt_bundle_old_path

libQtNetworkPatchingSedScript="s|$crt_bundle_old_path|$crt_bundle_new_path|"

patch_rodata $APPDIR/usr/lib/libQt5Network.so.5 "$libQtNetworkPatchingSedScript"


cp $ICONFILE $APPDIR/usr/share/icons/hicolor/48x48/apps/kiwix-desktop.svg
mkdir -p $APPDIR/usr/share/applications
cp $DESKTOPFILE $APPDIR/usr/share/applications/kiwix-desktop.desktop

# get the aria2
wget --continue https://github.com/q3aql/aria2-static-builds/releases/download/v1.36.0/aria2-1.36.0-linux-gnu-64bit-build1.tar.bz2
mkdir -p $APPDIR/usr/bin/ && tar -C $APPDIR/usr/bin/ -xf aria2-1.36.0-linux-gnu-64bit-build1.tar.bz2 aria2-1.36.0-linux-gnu-64bit-build1/aria2c --strip-components=1
mkdir -p $APPDIR/etc/ssl/certs/ && tar -C $APPDIR/etc/ssl/certs/ -xf aria2-1.36.0-linux-gnu-64bit-build1.tar.bz2 aria2-1.36.0-linux-gnu-64bit-build1/ca-certificates.crt --strip-components=1

# Get linuxdeployqt
# Dispite the 'continuous' in the file name, it IS release 8
wget --continue https://github.com/probonopd/linuxdeployqt/releases/download/continuous/linuxdeployqt-continuous-x86_64.AppImage -O linuxdeployqt
chmod u+x linuxdeployqt

# Fill with all deps libs and so
./linuxdeployqt $APPDIR/usr/bin/kiwix-desktop -bundle-non-qt-libs -extra-plugins=imageformats,iconengines
# Fix the RPATH of QtWebEngineProcess [TODO] Fill a issue ?
patchelf --set-rpath '$ORIGIN/../lib' $APPDIR/usr/libexec/QtWebEngineProcess

cp $DESKTOPFILE $APPDIR/kiwix-desktop.desktop
cp $ICONFILE $APPDIR/
cp $ICONFILE $APPDIR/.DirIcon

rm "$APPDIR"/AppRun

cat > "$APPDIR"/AppRun <<'END'
#!/usr/bin/env bash

mydir=$(dirname "$0")
mydir=$(cd "$mydir" && pwd)

crt_path=??? # this is set by postprocessing via sed

if [ ! -e "$crt_path" ]
then
    ln -s "$mydir"/etc/ssl/certs/ca-certificates.crt "$crt_path"
    trap "rm '$crt_path'" EXIT
fi

"$mydir"/usr/bin/kiwix-desktop "$@"
END

sed -i "s#^crt_path=.*#crt_path=$crt_bundle_new_path#" "$APPDIR"/AppRun

chmod 0755 "$APPDIR"/AppRun

wget --continue https://github.com/AppImage/AppImageKit/releases/download/13/appimagetool-x86_64.AppImage
chmod u+x appimagetool-x86_64.AppImage

./appimagetool-x86_64.AppImage AppDir Kiwix-"$VERSION"-x86_64.AppImage
