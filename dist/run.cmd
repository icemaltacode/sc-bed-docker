@echo off

goto(){
# ===== macOS / Linux section ======

# Exit on error
set -e

# ANSI colour codes
GREEN="\033[0;32m"
YELLOW="\033[1;33m"
RED="\033[0;31m"
RESET="\033[0m"

RESET_DB=0
VERBOSE=0

# Parse arguments
for arg in "$@"; do
  if [ "$arg" = "reset-db" ] || [ "$arg" = "--reset-db" ]; then
    RESET_DB=1
  fi
  if [ "$arg" = "--verbose" ] || [ "$arg" = "-v" ]; then
    VERBOSE=1
  fi
done

# ASCII art banner
echo
printf '%b\n' "${GREEN}  ___ ___ ___ ${RESET}"
printf '%b\n' "${GREEN} |_ _/ __| __|${RESET}"
printf '%b\n' "${GREEN}  | | (__| _| ${RESET}"
printf '%b\n' "${GREEN} |___\___|___|${RESET}"
printf '%b\n' "${YELLOW}    CAMPUS${RESET}"
echo

if [ $RESET_DB -eq 1 ]; then
  printf '%b\n' "${YELLOW}[info] Resetting database (docker compose down -v)...${RESET}"
  docker compose down -v || true
fi

if [ $VERBOSE -eq 1 ]; then
  printf '%b\n' "${YELLOW}[verbose] Project directory: $(pwd)${RESET}"
  printf '%b\n' "${YELLOW}[verbose] Docker compose config:${RESET}"
  docker compose config
  echo
fi

printf '%b\n' "${GREEN}Starting Server...${RESET}"
docker compose up

printf '%b\n' "${YELLOW}Destroying resources...${RESET}"
docker compose down

printf '%b\n' "${GREEN}Resources destroyed${RESET}"
}

goto "$@"
exit


:(){
REM ===== Windows section (CMD) =====

REM ANSI colours (Windows 10+ / Windows Terminal)
REM The funny-looking char before [32m is a real ESC (ASCII 27).
set "GREEN=[32m"
set "YELLOW=[33m"
set "RED=[31m"
set "RESET=[0m"

set RESET_DB=0
set VERBOSE=0

REM ---- Parse up to two arguments (no loops, no parentheses) ----
if "%1"=="reset-db"   set RESET_DB=1
if "%1"=="--reset-db" set RESET_DB=1

if "%1"=="--verbose"  set VERBOSE=1
if "%1"=="-v"         set VERBOSE=1
if "%2"=="--verbose"  set VERBOSE=1
if "%2"=="-v"         set VERBOSE=1

echo.
echo %GREEN%  ___ ___ ___ %RESET%
echo %GREEN% ^|_ _/ __^| __^|%RESET%
echo %GREEN%  ^| ^| (__^| _^| %RESET%
echo %GREEN% ^|___\___^|___^|%RESET%
echo %YELLOW%    CAMPUS%RESET%
echo.

REM ---- Handle reset-db without parentheses ----
if "%RESET_DB%"=="1" goto _reset_db
goto _after_reset_db

:_reset_db
echo %YELLOW%[info] Resetting database (docker compose down -v)...%RESET%
docker compose down -v
:_after_reset_db

REM ---- Handle verbose without parentheses ----
if "%VERBOSE%"=="1" goto _verbose
goto _after_verbose

:_verbose
echo %YELLOW%[verbose] Project directory: %CD%%RESET%
echo %YELLOW%[verbose] Docker compose config:%RESET%
docker compose config
echo.
:_after_verbose

echo %GREEN%Starting Server...%RESET%
docker compose up

echo %YELLOW%Destroying resources...%RESET%
docker compose down

echo %GREEN%Resources destroyed%RESET%
echo.
echo Press any key to exit...
pause >nul
exit
}