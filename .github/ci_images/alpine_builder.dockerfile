FROM alpine:3.16

ENV LANG C.UTF-8
ENV OS_NAME alpine

RUN apk update -q \
  && apk add -q --no-cache \
# Base build tools
        bash build-base git py3-pip \
# Packaged dependencies
        xz-dev \
        zstd-dev \
        xapian-core-dev \
        icu-dev icu-data-full \
        gtest-dev

# Create user
RUN adduser -h /home/runner -D runner
USER runner
WORKDIR /home/runner
ENV PATH /home/runner/.local/bin:$PATH
RUN pip3 install meson ninja ; \
    ln -s /usr/bin/python3 .local/bin/python
