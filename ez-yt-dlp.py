import os
import subprocess
import platform

# Determine the user's operating system
os_name = platform.system()

# Check if pip is installed
pip_installed = False
try:
    subprocess.run(['python', '-m', 'pip', 'install', '--upgrade', 'pip'], check=True)
    pip_installed = True
except:
    pass

if not pip_installed:
    if os_name == 'Windows':
        subprocess.run(['powershell', '-Command', 'Invoke-WebRequest -UseBasicParsing https://bootstrap.pypa.io/get-pip.py -OutFile get-pip.py'], check=True)
        subprocess.run(['python', 'get-pip.py', '--user'], check=True)
        os.environ['PATH'] += f';{os.path.expanduser("~")}\\AppData\\Roaming\\Python\\Python39\\Scripts'
    elif os_name == 'Linux':
        subprocess.run(['sudo', 'apt-get', 'install', '-y', 'python3-pip'], check=True)
    elif os_name == 'Darwin':
        subprocess.run(['curl', 'https://bootstrap.pypa.io/get-pip.py', '-o', 'get-pip.py'], check=True)
        subprocess.run(['sudo', 'python3', 'get-pip.py'], check=True)

# Install yt-dlp
subprocess.run(['pip', 'install', '--upgrade', 'yt-dlp'], check=True)

# Prompt user to paste the YouTube/Facebook/Odysee URL
url = input("Enter the YouTube/Facebook/Odysee URL to download: ")

# Ask user whether they are downloading video, video playlist, audio, and audio playlist
media_type = input("Enter media type (v, vp, a, ap): ")

if media_type == "v":
    media_format = "--format mp4"
    ext = ".mp4"
elif media_type == "vp":
    media_format = "--format mp4 --yes-playlist"
    ext = ".mp4"
elif media_type == "a":
    media_format = "--extract-audio --audio-format mp3 --audio-quality 0"
    ext = ".mp3"
elif media_type == "ap":
    media_format = "--extract-audio --audio-format mp3 --audio-quality 0 --yes-playlist"
    ext = ".mp3"
else:
    raise Exception("Unsupported media type")

# Ask where they want to save the download. The default directory should be Music and Video under user's directory consecutively
default_dir = os.path.join(os.path.expanduser('~'), 'Music' if media_type.startswith('a') else 'Videos')
dir_path = input(f"Enter save directory (default: {default_dir}): ")
if not dir_path:
    dir_path = default_dir

# Download media using yt-dlp
subprocess.run(f'yt-dlp {media_format} -o "{dir_path}/%(title)s{ext}" {url}', shell=True, check=True)

# Prompt user that the download has completed and is in a certain directory
print(f"Download complete. The file is at {dir_path}")
