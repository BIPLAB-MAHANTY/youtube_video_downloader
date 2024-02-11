from customtkinter import *
from pytube import YouTube
from pytube.exceptions import RegexMatchError
from PIL import Image
import urllib.request
import io
import math
# import ffmpeg
import subprocess
import os
import re

app = CTk()
app.title("Youtube Video Downloader")
app.geometry("500x400")
set_appearance_mode("system")


input_frame = CTkFrame(app)  # fg_color="transparent"
input_field = CTkEntry(input_frame, placeholder_text="Paste the YouTube url...",
                       text_color="#FFCC70", width=200, corner_radius=32)

invalid_label = None


def on_convert():
    youtube_url = input_field.get()
    global invalid_label
    if not is_valid_youtube_url(youtube_url) and youtube_url != "":
        invalid_label = CTkLabel(master=app, text="Invalid YouTube_Url",
                                 font=("Arial", 20), text_color="#FFCC70")

        invalid_label.place(relx=0.5, rely=0.3, relw=0.5, anchor="center")
    elif youtube_url == "":
        if invalid_label is not None:
            invalid_label.configure(text="")
    else:
        input_field.delete(0, END)
        input_frame.place_forget()

    second_frame(youtube_url)


def is_valid_youtube_url(url):
    try:
        YouTube(url)
        return True
    except RegexMatchError:
        return False


second_frame = ''


def second_frame(youtube_url):
    try:
        yt = YouTube(youtube_url)
        video_title = yt.title
        thumbnail_url = yt.thumbnail_url
        duration = yt.length  # Get duration in seconds

        # Handle different duration cases
        if duration > 3600:  # More than an hour
            hours, remainder = divmod(duration, 3600)
            minutes, seconds = divmod(remainder, 60)
            duration_str = f"{hours:02d}:{minutes:02d}:{seconds:02d}"
        elif duration > 60:  # Between 1 minute and 1 hour
            minutes, seconds = divmod(duration, 60)
            duration_str = f"{minutes:02d}:{seconds:02d}"
        else:  # Less than a minute
            seconds = duration
            duration_str = f"00:{seconds:02d}"

        global second_frame
        second_frame = CTkFrame(app)
        create_thumbnail(second_frame, thumbnail_url)
        rightside_frame = CTkFrame(second_frame)
        show_title(rightside_frame, video_title)
        show_duration(rightside_frame, duration_str)
        show_buttons(rightside_frame, youtube_url)

        rightside_frame.place(relx=0.4, rely=0.15, relw=0.5, relh=0.7)
        second_frame.place(relx=0.5, rely=0.3, relw=0.7,
                           relh=0.4, anchor="center")

    except Exception as e:
        return e


def create_thumbnail(root, thumbnail_url):

    # Get the thumbnail URL and download the image
    raw_data = urllib.request.urlopen(thumbnail_url).read()
    img = Image.open(io.BytesIO(raw_data))
    # Create a CTkImage object

    photo = CTkImage(light_image=img, dark_image=img, size=(200, 200))
    # Create a Label widget to display the image
    label = CTkLabel(root, image=photo, text="")

    # Place the Label widget in the root window
    label.pack(side="left", padx=20, pady=20)


def show_title(root, video_title):
    # Create a CTkLabel with an initial wraplength
    label = CTkLabel(root, text=video_title)
    label.pack(anchor="n", padx=10, pady=10)


def show_duration(root, duration_str):
    label = CTkLabel(root, text=duration_str)
    label.pack(anchor="n", padx=10, pady=(0, 10))


def show_options(youtube_url):
    yt = YouTube(youtube_url)
    video_options = ["Download Video"]
    audio_options = ["Download Audio"]
    for stream in yt.streams.filter(adaptive=True):
        size_str = convert_size(stream.filesize)
        if stream.resolution is not None:
            option = f"{stream.resolution} {stream.mime_type} - Size: {size_str}"
            video_options.append(option)
        else:
            option = f"{stream.abr} {stream.mime_type} - Size: {size_str}"
            audio_options.append(option)
    options = video_options + audio_options
    return options


def convert_size(size_bytes):
    if size_bytes == 0:
        return "0B"
    size_name = ("B", "KB", "MB", "GB", "TB", "PB", "EB", "ZB", "YB")
    i = int(math.floor(math.log(size_bytes, 1024)))
    p = math.pow(1024, i)
    s = round(size_bytes / p, 2)
    return f"{s} {size_name[i]}"


def show_buttons(root, youtube_url):

    options = show_options(youtube_url)
    option_menu = CTkOptionMenu(root, values=options, width=200)

    selected_option = ''

    def get_link():
        global selected_option
        selected_option = option_menu.get()
        if selected_option is not None:
            option_menu.destroy()
            get_link_btn.destroy()
            download_btn = CTkButton(
                root, text="Download", text_color="black", fg_color="yellow", command=download)

            convert_next_btn = CTkButton(root, text="Convert Next",
                                         text_color="black", fg_color="green", command=next_converion)
            download_btn.pack(side="left", padx=(70, 10), pady=10)
            convert_next_btn.pack(side="right", padx=(0, 50), pady=10)

    def next_converion():
        global second_frame
        second_frame.place_forget()
        input_frame.place(relx=0.5, rely=0.2, relw=0.5, anchor="center")

    def download():
        yt = YouTube(youtube_url)
        global selected_option
        highest_quality_audio = yt.streams.filter(
            only_audio=True).order_by('abr').desc().first()

        for stream in yt.streams.filter(adaptive=True):
            if (stream.type == "video" and stream.resolution in selected_option and stream.mime_type in selected_option and selected_option != "Download Video" and selected_option != "Download Audio"):
                video_file_extension = stream.mime_type.split(
                    '/')[-1]
                video_filename = f'video.{video_file_extension}'

                stream.download(filename=video_filename)

                audio_file_extension = highest_quality_audio.mime_type.split(
                    '/')[-1]

                audio_filename = f'audio.{audio_file_extension}'

                highest_quality_audio.download(filename=audio_filename)

                # Replace special characters and spaces in the title
                safe_title = re.sub('[^a-zA-Z0-9 \n\.]', '', yt.title)
                safe_title = safe_title.replace(' ', '_')

                output_filename = f'{safe_title}.mp4'

                subprocess.run(['ffmpeg', '-i', video_filename, '-i',
                               audio_filename, '-c', 'copy', output_filename])

                os.remove(video_filename)
                os.remove(audio_filename)
                break
            elif (stream.type == "audio" and stream.abr in selected_option and stream.mime_type in selected_option and selected_option != "Download Video" and selected_option != "Download Audio"):
                stream.download()
                break
            elif selected_option == "Download Video":
                highest_resolution_stream = yt.streams.filter(
                    adaptive=True, only_video=True).order_by("resolution").desc().first()

                video_file_extension = highest_resolution_stream.mime_type.split(
                    '/')[-1]

                video_filename = f'video.{video_file_extension}'

                highest_resolution_stream.download(filename=video_filename)

                audio_file_extension = highest_quality_audio.mime_type.split(
                    '/')[-1]

                audio_filename = f'audio.{audio_file_extension}'

                highest_quality_audio.download(filename=audio_filename)

                # Replace special characters and spaces in the title
                safe_title = re.sub('[^a-zA-Z0-9 \n\.]', '', yt.title)
                safe_title = safe_title.replace(' ', '_')

                output_filename = f'{safe_title}.mp4'

                subprocess.run(['ffmpeg', '-i', video_filename, '-i',
                               audio_filename, '-c', 'copy', output_filename])

                os.remove(video_filename)
                os.remove(audio_filename)
                break
            elif selected_option == "Download Audio":
                highest_quality_audio.download()
                break

    get_link_btn = CTkButton(root, text="get link",
                             fg_color="green", command=get_link)
    option_menu.pack(side="left", padx=(70, 10), pady=10)
    get_link_btn.pack(side="right", padx=(0, 50), pady=10)


btn = CTkButton(master=input_frame, text="Convert", corner_radius=32, fg_color="#4158D0",
                hover_color="#C850C0", border_color="#FFCC70", border_width=2, width=150,
                command=on_convert)


input_field.pack(side="left", padx=20, pady=20)
btn.pack(side="right", padx=20, pady=20)  # Position button to the right

# Center the input_frame itself using place
input_frame.place(relx=0.5, rely=0.2, relw=0.5, anchor="center")

app.mainloop()
