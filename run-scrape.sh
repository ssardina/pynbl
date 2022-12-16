#!/bin/bash
#
# Runs an update of the NBL stats

##### GET OPTIONS FROM COMMAND-LINE
NO_ARGS=$#   # Get the number of arguments passed in the command line
MY_NAME=${0##*/} 
DIR_SCRIPT=`dirname $0` # Find path of the current script


##### SCRIPT STARTS HERE
now=`date +"%Y-%m-%d--%H:%M"`
log_file="backup-ssardina-${now}.log"
EXCLUDE_FILE="~/rsync-exclude-home.txt"


cd "$DIR_SCRIPT"
python -m nbl.nbl_scrapper --games games_22_23 --data test --save






