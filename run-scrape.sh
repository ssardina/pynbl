#!/bin/bash
#
# Runs an update of the NBL stats and saves files in a Google Drive folder
#   Script first mounts a Google Drive folder into gdrive/ using 
#     google-drive-ocamlfuse (https://github.com/astrada/google-drive-ocamlfuse/)
#       and then scrapes the stats and saves the files in that folder. It unmounts then.
#

##### GET OPTIONS FROM COMMAND-LINE
NO_ARGS=$#   # Get the number of arguments passed in the command line
MY_NAME=${0##*/}
DIR_SCRIPT=`dirname $0` # Find path of the current script


##### SCRIPT STARTS HERE
now=`date +"%Y-%m-%d--%H:%M"`
log_file="backup-ssardina-${now}.log"

cd "$DIR_SCRIPT"
google-drive-ocamlfuse gdrive   # mount gdrive
python -m nbl.nbl_scrapper --games games_22_23 --data gdrive $@
sleep 25    # wait for a while so there are no locks before unmounting

x=1
while [ $x -gt 0 ];
do
    sleep 10
    echo "Unmounting gdrive..."
    fusermount -u gdrive
    x=$?
    echo "Exit $x"
done









