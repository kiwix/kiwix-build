FROM ubuntu:bionic

ENV LANG C.UTF-8

RUN apt update -q && \
    apt install -q -y --no-install-recommends \
# Base build tools
    build-essential automake libtool cmake ccache pkg-config autopoint patch \
    python3-pip python3-setuptools python3-wheel git subversion wget unzip \
    ninja-build \
# Packaged dependencies
    libbz2-dev libmagic-dev uuid-dev zlib1g-dev \
    libmicrohttpd-dev aria2 \
# Qt packages
    libqt5gui5 qtbase5-dev qtwebengine5-dev libqt5svg5-dev qt5-image-formats-plugins qt5-default \
# To create the appimage of kiwix-desktop
    libfuse2 fuse patchelf \
# Flatpak tools
    elfutils flatpak flatpak-builder \
# Cross win32 compiler
    g++-mingw-w64-i686 gcc-mingw-w64-i686 gcc-mingw-w64-base mingw-w64-tools \
# Other tools (to remove)
#    vim less grep \
  && \
  apt-get clean -y && \
  rm -rf /var/lib/apt/lists/* /usr/share/doc/* /var/cache/debconf/*

# Create user
RUN useradd --create-home ci_builder
USER ci_builder
WORKDIR /home/ci_builder
ENV PATH="/home/ci_builder/.local/bin:${PATH}"

ENV TRAVIS_BUILD_DIR /home/ci_builder/kiwix-build
ENV TRAVIS_OS_NAME linux_bionic

CMD pip3 install --user ./kiwix-build && kiwix-build/travis/compile_all.py
