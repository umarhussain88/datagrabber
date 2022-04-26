#!/bin/bash -l
source $HOME/.bashrc
cd /home/umarh/datagrabber
start_datetime=$(date '+%m_%d_%Y_%H_%M_%S')
echo "${start_datetime}"
export LC_ALL=en_US.utf-8
echo "running main.py"
/usr/local/bin/pipenv run python3 main.py kajabi
end_datetime=$(date '+%m_%d_%Y_%H_%M_%S')
echo "${end_datetime} - script finished successfully"