FROM ubuntu:bionic

ENV LANG C.UTF-8

RUN apt update -q && \
    apt install -q -y --no-install-recommends \
# Base build tools
    python3-pip python3-setuptools git patch unzip xz-utils gzip ninja-build \
# Flatpak tools
    elfutils flatpak flatpak-builder \
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
