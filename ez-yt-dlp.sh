#!/bin/bash
# This is in very early stage. Let's say this is my hobby project. So, definetely
# will be updates comming every week, month or year.

clear
cat << EOF
Please Select:

    1. Download Single YouTube Video
    2. Download Single YouTube Audio
    3. Download YouTube Video Playlist
    4. Download YouTube Audio Playlist
    5. Quit

EOF
echo -n "Enter one at a time [1-5]: "
read -r sel

case $sel in
    1) read -p "Enter URL here: " URL && yt-dlp -o "%(title)s.%(ext)s" $URL ;;
    2) read -p "Enter URL here: " URL && yt-dlp --extract-audio --audio-format mp3 -o "%(title)s.%(ext)s" $URL ;;
    3) read -p "Enter URL here: " URL && yt-dlp --yes-playlist -o "%(title)s.%(ext)s" $URL ;;
    4) read -p "Enter URL here: " URL && yt-dlp --yes-playlist --extract-audio --audio-format mp3 -o "%(title)s.%(ext)s" $URL ;;
    5) echo "Quiting now.." ;;
    *)
        echo "Invalid input. Exiting.." >&2
        exit 1
esac
