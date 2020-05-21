FROM fedora:31

ENV LANG C.UTF-8
ENV OS_NAME f31

RUN dnf install -y --nodocs \
# Base build tools
    make automake libtool cmake git-core subversion pkg-config gcc-c++ \
    wget unzip ninja-build ccache which patch gcovr xz openssh-clients \
# Cross win32 compiler
    mingw32-gcc-c++ mingw32-bzip2-static mingw32-win-iconv-static \
    mingw32-winpthreads-static mingw32-zlib-static mingw32-xz-libs-static \
    mingw32-libmicrohttpd \
# python3
    python3-pip python-unversioned-command \
# Other tools (to remove)
#    vim less grep
  && dnf remove -y "*-doc" \
  && dnf autoremove -y \
  && dnf clean all \
  && pip3 install meson==0.52.1 pytest requests

# Create user
RUN useradd --create-home runner
USER runner
WORKDIR /home/runner
ENV PATH /home/runner/.local/bin:$PATH
