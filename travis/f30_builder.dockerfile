FROM fedora:30

ENV LANG C.UTF-8

RUN dnf install -y --nodocs \
# Base build tools
    make automake libtool cmake git-core subversion pkg-config gcc-c++ \
    wget unzip ninja-build ccache which patch \
# Cross win32 compiler
    mingw32-gcc-c++ mingw32-bzip2-static mingw32-win-iconv-static \
    mingw32-winpthreads-static mingw32-zlib-static mingw32-xz-libs-static \
    mingw32-libmicrohttpd \
# Other tools (to remove)
#    vim less grep
  && dnf remove -y "*-doc" \
  && dnf autoremove -y \
  && dnf clean all

# Create user
RUN useradd --create-home ci_builder
USER ci_builder
WORKDIR /home/ci_builder
ENV PATH="/home/ci_builder/.local/bin:${PATH}"

ENV TRAVIS_BUILD_DIR /home/ci_builder/kiwix-build
ENV TRAVIS_OS_NAME linux_f30

CMD pip3 install --user ./kiwix-build && kiwix-build/travis/compile_all.py
