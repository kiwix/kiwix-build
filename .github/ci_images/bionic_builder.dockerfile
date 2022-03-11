FROM ubuntu:bionic

ENV LANG C.UTF-8
ENV OS_NAME bionic

RUN apt update -q \
  && dpkg --add-architecture i386 \
  && apt install -q -y --no-install-recommends software-properties-common \
  && add-apt-repository ppa:beineri/opt-qt-5.15.2-bionic \
  && apt-get update \
  && apt install -q -y --no-install-recommends \
# Base build tools
    build-essential automake libtool cmake ccache pkg-config autopoint patch \
    python3-pip python3-setuptools python3-wheel git subversion wget unzip \
    ninja-build openssh-client curl libgl-dev \
# Python (2) is needed to install android-ndk
    python \
# Packaged dependencies
    libbz2-dev libmagic-dev uuid-dev zlib1g-dev default-jdk \
    libmicrohttpd-dev aria2 libgtest-dev libgl-dev \
# Qt packages
    qt515base qt515webengine qt515svg qt515imageformats qt515wayland \
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
  && pip3 install meson pytest gcovr requests distro

# Create user
RUN useradd --create-home runner
USER runner
WORKDIR /home/runner
ENV PATH /home/runner/.local/bin:$PATH

# Set qt515 environment (the equivalent of "source /opt/qt515/bin/qt515-env.sh")
# RUN echo "source /opt/qt515/bin/qt515-env.sh" >> /home/runner/.bashrc
ENV PATH=/opt/qt515/bin:$PATH \
    LD_LIBRARY_PATH=/opt/qt515/lib/x86_64-linux-gnu:/opt/qt515/lib:$LD_LIBRARY_PATH \
    PKG_CONFIG_PATH=/opt/qt515/lib/pkgconfig:$PKG_CONFIG_PATH
