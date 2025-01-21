import os
import cv2
import tkinter as tk
from tkinter import filedialog
from PIL import Image, ImageTk
from tkinter import simpledialog

class VideoThumbnailApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Video Thumbnail Creator")
        
        # Directory and video variables
        self.video_directory = ""
        # Set default thumbnail directory to a folder named "thumbnails" in the current working directory
        self.thumbnail_directory = os.path.join(os.getcwd(), "F:/booru app/static/thumbnails")
        
        # Ensure the default thumbnail directory exists
        if not os.path.exists(self.thumbnail_directory):
            os.makedirs(self.thumbnail_directory)

        self.video_files = []
        self.current_video_index = 0
        self.cap = None
        self.paused = True

        # Create GUI layout
        self.create_widgets()

    def create_widgets(self):
        # Video frame where video will be displayed
        self.video_label = tk.Label(self.root)
        self.video_label.grid(row=0, column=0, columnspan=5)

        # Previous, Play/Pause, Create Thumbnail, and Next buttons
        self.prev_button = tk.Button(self.root, text="Previous video", command=self.prev_video)
        self.prev_button.grid(row=1, column=0)

        self.play_pause_button = tk.Button(self.root, text="Play", command=self.toggle_play_pause)
        self.play_pause_button.grid(row=1, column=1)

        self.create_button = tk.Button(self.root, text="Create thumbnail", command=self.create_thumbnail)
        self.create_button.grid(row=1, column=2)

        self.next_button = tk.Button(self.root, text="Next video", command=self.next_video)
        self.next_button.grid(row=1, column=3)

        # Step Backward and Step Forward buttons
        self.step_backward_button = tk.Button(self.root, text="Step Backward", command=self.step_backward)
        self.step_backward_button.grid(row=2, column=0)

        self.step_forward_button = tk.Button(self.root, text="Step Forward", command=self.step_forward)
        self.step_forward_button.grid(row=2, column=1)

        # Slider for navigating video time
        self.slider = tk.Scale(self.root, from_=0, to=100, orient=tk.HORIZONTAL, label="Video position (seconds)", command=self.update_video_position)
        self.slider.grid(row=3, column=0, columnspan=5, sticky='we')

        # Open directory dialog to load videos
        self.open_dir_button = tk.Button(self.root, text="Open Video Directory", command=self.open_video_directory)
        self.open_dir_button.grid(row=4, column=0, columnspan=5)

        # Create thumbnail directory dialog
        self.set_thumbnail_dir_button = tk.Button(self.root, text="Set Thumbnail Directory", command=self.set_thumbnail_directory)
        self.set_thumbnail_dir_button.grid(row=5, column=0, columnspan=5)

        self.update_video()

    def open_video_directory(self):
        self.video_directory = filedialog.askdirectory(title="Select Video Directory")
        if self.video_directory:
            self.video_files = [f for f in os.listdir(self.video_directory) if f.endswith(('.mp4', '.avi', '.mov', '.mkv'))]
            self.current_video_index = 0
            self.load_video()

    def set_thumbnail_directory(self):
        # Let user select thumbnail directory
        selected_directory = filedialog.askdirectory(title="Select Thumbnail Directory")
        if selected_directory:
            self.thumbnail_directory = selected_directory

    def load_video(self):
        if not self.video_files:
            return

        video_path = os.path.join(self.video_directory, self.video_files[self.current_video_index])
        self.cap = cv2.VideoCapture(video_path)

        if self.cap.isOpened():
            total_frames = int(self.cap.get(cv2.CAP_PROP_FRAME_COUNT))
            fps = int(self.cap.get(cv2.CAP_PROP_FPS))
            total_duration = total_frames // fps
            self.slider.config(to=total_duration)
            self.paused = True
            self.play_pause_button.config(text="Play")
            self.update_video()

    def update_video(self):
        if self.cap and self.cap.isOpened() and not self.paused:
            success, frame = self.cap.read()
            if success:
                # Convert the frame to a format tkinter can display
                frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                image = Image.fromarray(frame)
                image = image.resize((640, 360), Image.Resampling.LANCZOS)
                photo = ImageTk.PhotoImage(image)
                self.video_label.config(image=photo)
                self.video_label.image = photo

                # Auto-update video position on the slider
                current_pos = self.cap.get(cv2.CAP_PROP_POS_FRAMES) / self.cap.get(cv2.CAP_PROP_FPS)
                self.slider.set(current_pos)

            self.root.after(30, self.update_video)

    def toggle_play_pause(self):
        if self.paused:
            self.paused = False
            self.play_pause_button.config(text="Pause")
        else:
            self.paused = True
            self.play_pause_button.config(text="Play")
        self.update_video()

    def update_video_position(self, event):
        if self.cap and self.cap.isOpened():
            target_time = self.slider.get()
            self.cap.set(cv2.CAP_PROP_POS_MSEC, target_time * 1000)
            self.display_current_frame()

    def prev_video(self):
        if self.video_files:
            self.current_video_index = (self.current_video_index - 1) % len(self.video_files)
            self.load_video()

    def next_video(self):
        if self.video_files:
            self.current_video_index = (self.current_video_index + 1) % len(self.video_files)
            self.load_video()

    def create_thumbnail(self):
        if not self.cap or not self.thumbnail_directory:
            print("No video or thumbnail directory selected.")
            return
        
        # Ask for filename
        thumbnail_filename = simpledialog.askstring("Input", "Enter filename for the thumbnail (without extension):")
        if not thumbnail_filename:
            return

        # Get current frame position (in seconds)
        current_pos = self.cap.get(cv2.CAP_PROP_POS_MSEC) / 1000
        print(f"Creating thumbnail at {current_pos} seconds.")

        # Set the frame to the desired position
        self.cap.set(cv2.CAP_PROP_POS_MSEC, current_pos * 1000)
        success, frame = self.cap.read()

        if success:
            # Convert frame to image and save it
            frame_image = Image.fromarray(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
            thumbnail_path = os.path.join(self.thumbnail_directory, f"{thumbnail_filename}.jpg")
            frame_image.save(thumbnail_path)
            print(f"Thumbnail saved as {thumbnail_path}")

    def step_forward(self):
        if self.cap and self.cap.isOpened():
            # Get the current frame position and increment by 1
            current_frame = self.cap.get(cv2.CAP_PROP_POS_FRAMES)
            self.cap.set(cv2.CAP_PROP_POS_FRAMES, current_frame + 1)
            self.display_current_frame()

    def step_backward(self):
        if self.cap and self.cap.isOpened():
            # Get the current frame position and decrement by 1
            current_frame = self.cap.get(cv2.CAP_PROP_POS_FRAMES)
            if current_frame > 0:
                self.cap.set(cv2.CAP_PROP_POS_FRAMES, current_frame - 1)
                self.display_current_frame()

    def display_current_frame(self):
        if self.cap and self.cap.isOpened():
            success, frame = self.cap.read()
            if success:
                frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                image = Image.fromarray(frame)
                image = image.resize((640, 360), Image.Resampling.LANCZOS)
                photo = ImageTk.PhotoImage(image)
                self.video_label.config(image=photo)
                self.video_label.image = photo

            # Update the slider to reflect the new frame position
            current_pos = self.cap.get(cv2.CAP_PROP_POS_FRAMES) / self.cap.get(cv2.CAP_PROP_FPS)
            self.slider.set(current_pos)

# Create the main window
root = tk.Tk()
app = VideoThumbnailApp(root)
root.mainloop()
