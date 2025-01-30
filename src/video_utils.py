# pylint: disable=missing-module-docstring
# pylint: disable=missing-function-docstring

## for local server

# import os
# import shutil
# import subprocess
# import tempfile
# import telegram
# from dotenv import load_dotenv
# from logger import print_logs

# load_dotenv()

# ffprobe_path = os.getenv("FFPROBE_PATH")

# def compress_video(input_path):
#     """
#     Compress video for 50MB with use of FFmpeg.
    
#     Parameters:
#         input_path (str): Path to original video.
#     """

#     temp_output = tempfile.mktemp(suffix=".mp4")
#     # Caclulation of file size. 40 means MB
#     target_size_bytes = 40 * 1024 * 1024
#     duration = get_video_duration(input_path)
#     if not duration:
#         raise ValueError("Get video duration failed")

#     # bitrate caclulation kb/s (bit/sec -> kb/sec)
#     target_bitrate_kbps = (target_size_bytes * 8) / duration / 1000

#     command = [
#         "ffmpeg",
#         "-i", input_path,
#         "-b:v", f"{target_bitrate_kbps}k",
#         "-vf", "scale=-2:720",
#         "-c:v", "libx265",     
#         "-preset", "fast",      
#         "-c:a", "aac",         
#         "-b:a", "128k",         
#         "-y",                   
#         temp_output
#     ]

#     try:
#         subprocess.run(command, check=True)
#         if os.path.exists(temp_output):
#             os.replace(temp_output, input_path)
#             print(f"Compressed done. File saved: {input_path}")
#     except subprocess.CalledProcessError as e:
#         print(f"Error while compressing: {e}")

# def get_video_duration(video_path):
#     """
#     Gets video duration in seconds.
#     """
#     command = [
#         ffprobe_path,
#         "-v", "error",
#         "-show_entries", "format=duration",
#         "-of", "default=noprint_wrappers=1:nokey=1",
#         video_path
#     ]
#     try:
#         result = subprocess.run(
#             command,
#             stdout=subprocess.PIPE,
#             stderr=subprocess.PIPE,
#             text=True,
#             check=True
#         )
#         return float(result.stdout.strip())
#     except telegram.error.TelegramError as e:
#         print(f"Error getting video duration: {e}")
#         return None

# def download_video(url):
#     temp_dir = tempfile.mkdtemp()
#     command = [
#         "yt-dlp.exe",
#         "--ffmpeg-location", "ffmpeg.exe",
#         "-S", "vcodec:h264,fps,res,acodec:m4a",
#         url,
#         "-o", os.path.join(temp_dir, "%(id)s.%(ext)s")
#     ]

#     try:
#         subprocess.run(command, check=True, timeout=120)

#         for filename in os.listdir(temp_dir):
#             if filename.endswith(".mp4"):
#                 return os.path.join(temp_dir, filename)
#         return None
#     except subprocess.CalledProcessError as e:
#         print_logs(f"Download process error: {e.stderr}")
#         return None
#     except subprocess.TimeoutExpired as e:
#         print_logs(f"Download timeout after {e.timeout}s")
#         return None
#     except (OSError, ValueError, RuntimeError) as e:
#         print_logs(f"System error during download: {e}")
#         return None

# def cleanup_file(video_path):
#     print_logs(f"Video to delete {video_path}")
#     try:
#         shutil.rmtree(os.path.dirname(video_path))
#         print_logs(f"Video deleted {video_path}")
#     except (OSError, PermissionError) as cleanup_error:
#         print_logs(f"Error deleting file: {cleanup_error}")


## for online server


import os
import shutil
import subprocess
import tempfile
import telegram
from dotenv import load_dotenv
from logger import print_logs

load_dotenv()

# On Replit, ffprobe and ffmpeg should be installed and accessible from PATH.
ffprobe_path = "ffprobe"  # Use 'ffprobe' command in Replit environment


def compress_video(input_path):
    """
    Compress video for 50MB with the use of FFmpeg.

    Parameters:
        input_path (str): Path to original video.
    """
    temp_output = tempfile.mktemp(suffix=".mp4")
    # Calculation of file size. 40 means MB
    target_size_bytes = 40 * 1024 * 1024
    duration = get_video_duration(input_path)
    if not duration:
        raise ValueError("Get video duration failed")

    # Bitrate calculation kb/s (bit/sec -> kb/sec)
    target_bitrate_kbps = (target_size_bytes * 8) / duration / 1000

    command = [
        "ffmpeg",  # Using 'ffmpeg' command installed on Replit
        "-i",
        input_path,
        "-b:v",
        f"{target_bitrate_kbps}k",
        "-vf",
        "scale=-2:720",
        "-c:v",
        "libx265",
        "-preset",
        "fast",
        "-c:a",
        "aac",
        "-b:a",
        "128k",
        "-y",
        temp_output
    ]

    try:
        subprocess.run(command, check=True)
        if os.path.exists(temp_output):
            os.replace(temp_output, input_path)
            print(f"Compressed done. File saved: {input_path}")
    except subprocess.CalledProcessError as e:
        print(f"Error while compressing: {e}")


def get_video_duration(video_path):
    """
    Gets video duration in seconds.
    """
    command = [
        ffprobe_path,  # Use the 'ffprobe' command on Replit
        "-v",
        "error",
        "-show_entries",
        "format=duration",
        "-of",
        "default=noprint_wrappers=1:nokey=1",
        video_path
    ]
    try:
        result = subprocess.run(command,
                                stdout=subprocess.PIPE,
                                stderr=subprocess.PIPE,
                                text=True,
                                check=True)
        return float(result.stdout.strip())
    except telegram.error.TelegramError as e:
        print(f"Error getting video duration: {e}")
        return None


def download_video(url):
    temp_dir = tempfile.mkdtemp()
    command = [
        "yt-dlp",  # Use 'yt-dlp' installed on Replit
        "--ffmpeg-location",
        "ffmpeg",  # Path to ffmpeg (no need to use 'ffmpeg.exe')
        "-S",
        "vcodec:h264,fps,res,acodec:m4a",
        url,
        "-o",
        os.path.join(temp_dir, "%(id)s.%(ext)s")
    ]

    try:
        subprocess.run(command, check=True, timeout=120)

        for filename in os.listdir(temp_dir):
            if filename.endswith(".mp4"):
                return os.path.join(temp_dir, filename)
        return None
    except subprocess.CalledProcessError as e:
        print_logs(f"Download process error: {e.stderr}")
        return None
    except subprocess.TimeoutExpired as e:
        print_logs(f"Download timeout after {e.timeout}s")
        return None
    except (OSError, ValueError, RuntimeError) as e:
        print_logs(f"System error during download: {e}")
        return None


def cleanup_file(video_path):
    print_logs(f"Video to delete {video_path}")
    try:
        shutil.rmtree(os.path.dirname(video_path))
        print_logs(f"Video deleted {video_path}")
    except (OSError, PermissionError) as cleanup_error:
        print_logs(f"Error deleting file: {cleanup_error}")
