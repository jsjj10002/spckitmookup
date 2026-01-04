@echo off
cd /d "c:\Users\nrtak\Desktop\testing\1\spckitmookup"
git status > git_status.txt 2>&1
git log --no-pager -n 5 --stat frontend > git_log.txt 2>&1
dir frontend > dir_log.txt 2>&1
echo DONE
