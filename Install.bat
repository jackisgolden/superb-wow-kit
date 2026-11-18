@echo off
title Superb WoW Kit
powershell -NoProfile -ExecutionPolicy Bypass -Command "[Net.ServicePointManager]::SecurityProtocol='Tls12'; & ([scriptblock]::Create((Invoke-RestMethod -UseBasicParsing 'https://raw.githubusercontent.com/jackisgolden/superb-wow-kit/main/install.ps1')))"
echo.
pause
