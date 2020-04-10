REM ========================================================
REM Install kiwix-desktop
git clone https://github.com/kiwix/kiwix-desktop || exit /b 1
cd kiwix-desktop
echo "Running qmake"
C:\Qt\5.12\msvc2017_64\bin\qmake.exe "CONFIG+=static" || exit /b 1
echo "Running fix_desktop"
C:\Python36\Python ..\appveyor\fix_desktop_makefile.py Makefile.Release || exit /b 1
echo "Running nmake"
nmake || exit /b 1
cd ..
