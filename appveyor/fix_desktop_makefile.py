import re, sys, os

makefile = sys.argv[-1]
print("Patching '{}'".format(makefile))

with open(makefile, 'r') as f:
    lines = f.readlines()

with open(makefile, 'w') as f:
    for line in lines:
#        if "/SUBSYSTEM:WINDOWS" in line:
#            line = line.replace("/SUBSYSTEM:WINDOWS", "/SUBSYSTEM:CONSOLE")
#            f.write(line)
#            continue
        if not line.startswith('LIBS  '):
            f.write(line)
            continue
        print("-- INPUT : {}".format(line))
        for lib in ('kiwix', 'zim', 'pugixml', 'z', 'zstd'):
            line = line.replace('{}.lib'.format(lib), 'lib{}.a'.format(lib))
        for lib in ('lzma', 'curl'):
            line = line.replace('lib{}.lib'.format(lib), 'lib{}.a'.format(lib))
        line = line.strip()
#        line += " pthreadVC2.lib"
#        line += " icuin.lib icudt.lib icuuc.lib"
        line += " Rpcrt4.lib Ws2_32.lib winmm.lib Shlwapi.lib"
        line += os.linesep
        print("++ OUTPUT : {}".format(line))
        f.write(line)
