import os
import subprocess
import sys

def check_installation():
    try:
        # Check if yt-dlp is installed
        subprocess.run(['pacman', '-Qq'], check=True, text=True, capture_output=True)
    except subprocess.CalledProcessError:
        print("yt-dlp not found. Installing...")
        try:
            subprocess.run(['sudo', 'pacman', '-Syu', '--noconfirm', 'yt-dlp'], check=True)
        except subprocess.CalledProcessError:
            print("Failed to install yt-dlp. Exiting.")
            sys.exit(1)

def download_media(option, url, save_dir):
    # Define options based on user choice
    if option == 'v':
        ext = '.mp4'
        yt_options = '-f bestvideo+bestaudio'
    elif option == 'vp':
        ext = '.mp4'
        yt_options = '-f bestvideo+bestaudio --yes-playlist'
    elif option == 'a':
        ext = '.mp3'
        yt_options = '--extract-audio --audio-format mp3 --audio-quality 0'
    elif option == 'ap':
        ext = '.mp3'
        yt_options = '--yes-playlist --extract-audio --audio-format mp3 --audio-quality 0'
    else:
        print("Invalid option selected.")
        return
    
    # Ensure the save directory exists
    os.makedirs(save_dir, exist_ok=True)
    
    # Build the command
    command = ['yt-dlp', yt_options, '-o', f"{save_dir}/%(title)s{ext}", url]
    
    try:
        subprocess.run(command, check=True)
        print(f"Download successful! File saved to {save_dir}")
    except subprocess.CalledProcessError:
        print("Download failed. Please check your URL and try again.")

def main():
    check_installation()
    
    while True:
        print("""
Please choose Media Download Option:

      v - Download Single Video
      vp - Download Video Playlist
      a - Download Single Audio
      ap - Download Audio Playlist
      q - Quit
""")
        
        option = input("Enter your choice (v, vp, a, ap, q): ").strip()
        
        if option == 'q':
            print("Quitting...")
            sys.exit(0)
        
        url = input("Enter the YouTube/Facebook/Odysee URL: ").strip()
        if not url.startswith(('http://', 'https://')):
            print("Invalid URL. Please enter a valid URL starting with http:// or https://")
            continue
        
        save_dir = input(f"Enter Save directory ($HOME/Videos): ").strip()
        save_dir = save_dir or os.path.expanduser('~/Videos')
        
        download_media(option, url, save_dir)

if __name__ == "__main__":
    main()
