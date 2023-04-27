FROM ubuntu:bionic

ENV LANG C.UTF-8
ENV OS_NAME bionic

RUN apt update -q \
  && apt-get update \
  && apt install -q -y --no-install-recommends \
# Base build tools
    build-essential automake libtool cmake ccache pkg-config autopoint patch \
    python3-pip python3-setuptools python3-wheel git subversion wget unzip \
    ninja-build openssh-client curl \
# Packaged dependencies
    libbz2-dev uuid-dev zlib1g-dev \
    libgtest-dev \
# Other tools (to remove)
#    vim less grep \
  && apt-get clean -y \
  && rm -rf /var/lib/apt/lists/* /usr/share/doc/* /var/cache/debconf/* \
  && pip3 install meson pytest gcovr requests distro

# Create user
RUN groupadd --gid 121 runner
RUN useradd --uid 1001 --gid 121 --create-home runner
USER runner
ENV PATH /home/runner/.local/bin:$PATH
