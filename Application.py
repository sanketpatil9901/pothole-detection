import tkinter as tk
import customtkinter
import imageDetector
import videoDetector
from tkinter import Label
from tkinter import filedialog as fd
from tkinter.messagebox import showinfo

customtkinter.set_appearance_mode("System")  # Modes: system (default), light, dark
customtkinter.set_default_color_theme("green")  # Themes: blue (default), dark-blue, green

# create the root window
root = customtkinter.CTk()
root.title('Potholes Detection')
root.resizable(False, False)
root.geometry('400x200')
result_label = customtkinter.CTkLabel(root, text="", justify="left", width=380, wraplength=380, font=("poppins", 12))
result_label.pack(pady=(10, 0))


HeadingText= Label(root, text="Select Image or Video to Identify Pothole", font=("poppins", 16))


def show_pothole_results(count, details):
    result_window = customtkinter.CTkToplevel(root)
    result_window.title("Detection Results")
    result_window.geometry("500x400")
    result_window.resizable(False, False)

    header = customtkinter.CTkLabel(result_window, text=f"Potholes Detected: {count}", font=("poppins", 16, "bold"))
    header.pack(pady=10)

    frame = customtkinter.CTkScrollableFrame(result_window, width=450, height=300)
    frame.pack(pady=5, padx=10)

    for i, pothole in enumerate(details, start=1):
        text = f"Pothole {i}:\n"
        text += f"• Confidence: {pothole['confidence']}%\n"
        text += f"• Position: {pothole['position']}\n"
        text += f"• Size: {pothole['size']}\n"

        label = customtkinter.CTkLabel(frame, text=text, anchor="w", justify="left", font=("poppins", 12), text_color="white")
        label.pack(pady=5, anchor="w")


def select_image_file():
    filetypes = (('Image files', '*.jpg'),)
    filename = fd.askopenfilename(title='Open a file', initialdir='/', filetypes=filetypes)

    if len(filename) > 0:
        showinfo(title='Selected Image File', message=filename)
        count, details = imageDetector.detectPotholeonImage(filename)
        show_pothole_results(count, details)



def select_video_file():
    #Restricting only Image and video files to select through application
    filetypes = (('Video files', '*.mp4'),)

    filename = fd.askopenfilename(
        title='Open a file',
        initialdir='/',
        filetypes=filetypes)

    if(len(filename)) > 0:
        showinfo(title='Selected Video File',message=filename)
        videoDetector.detectPotholeonVideo(filename)



#Image open button
image_open_button = customtkinter.CTkButton(root,text='Image',command=select_image_file,hover_color="green")

#Video open button
video_open_button = customtkinter.CTkButton(root,text='Video',command=select_video_file,hover_color="green")

#Live Camera button
liveCamera_button = customtkinter.CTkButton(root,
                                            text='Live Camera',
                                            command= lambda : videoDetector.detectPotholeonVideo(0),
                                            hover_color="green",
                                            border_color="black",
                                            border_width=2.5,
                                            fg_color= "red",font=("poppins", 14))


HeadingText.place(x= 50, y =15)
image_open_button.place(x=40, y=80)
video_open_button.place(x=220, y=80)
liveCamera_button.pack(side='bottom',pady=20)


# run the application
root.mainloop()
