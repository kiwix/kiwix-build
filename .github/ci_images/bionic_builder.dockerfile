FROM ubuntu:bionic

ENV LANG C.UTF-8
ENV OS_NAME bionic

RUN apt update -q \
  && dpkg --add-architecture i386 \
  && apt install -q -y --no-install-recommends \
# Base build tools
    build-essential automake libtool cmake ccache pkg-config autopoint patch \
    python3-pip python3-setuptools python3-wheel git subversion wget unzip \
    ninja-build openssh-client curl \
# Python (2) is needed to install android-ndk
    python \
# Packaged dependencies
    libbz2-dev libmagic-dev uuid-dev zlib1g-dev default-jdk \
    libmicrohttpd-dev aria2 libgtest-dev \
# Qt packages
    libqt5gui5 qtbase5-dev qtwebengine5-dev libqt5svg5-dev qt5-image-formats-plugins qt5-default \
# To create the appimage of kiwix-desktop
    libfuse2 fuse patchelf \
# Flatpak tools
    elfutils flatpak flatpak-builder \
# Cross compile i586
    libc6-dev-i386 lib32stdc++6 gcc-multilib g++-multilib \
# Other tools (to remove)
#    vim less grep \
  && apt-get clean -y \
  && rm -rf /var/lib/apt/lists/* /usr/share/doc/* /var/cache/debconf/* \
  && pip3 install meson==0.52.1 pytest gcovr requests distro

# Create user
RUN useradd --create-home runner
USER runner
WORKDIR /home/runner
ENV PATH /home/runner/.local/bin:$PATH
