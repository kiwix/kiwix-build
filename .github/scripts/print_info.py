#!/usr/bin/env python3

import os, platform, sys, sysconfig


def print_info(what):
    value = eval(what)
    print(f"{what} : {value}")


print_info("os.uname()")
print_info("platform.architecture()")
print_info("platform.machine()")
print_info("platform.platform()")
print_info("platform.processor()")
print_info("platform.uname()")
print_info("sys.abiflags")
print_info("sys.platform")
print_info("sysconfig.get_platform()")
