@echo off
chcp 65001 > nul
echo %PATH% > path_debug.txt
where uv >> path_debug.txt 2>&1
echo Done. >> path_debug.txt
