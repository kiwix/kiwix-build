REM ========================================================
REM Install kiwix-desktop
git clone https://github.com/kiwix/kiwix-desktop || exit /b 1
cd kiwix-desktop
git checkout 2.3.1 || exit /b 1
echo "Running qmake"
SET _WITH_CONSOLE=1
IF %KIWIX_DESKTOP_RELEASE% EQU 1 (
  IF %APPVEYOR_REPO_TAG% == true (
    SET _WITH_CONSOLE=0
  )
)
IF %_WITH_CONSOLE% EQU 1 (
    C:\Qt\5.15\msvc2019_64\bin\qmake.exe "CONFIG+=static console" || exit /b 1
) else (
    C:\Qt\5.15\msvc2019_64\bin\qmake.exe "CONFIG+=static" || exit /b 1
)

echo "Running fix_desktop"
C:\Python36\Python ..\appveyor\fix_desktop_makefile.py Makefile.Release || exit /b 1
echo "Running nmake"
nmake || exit /b 1
cd ..
