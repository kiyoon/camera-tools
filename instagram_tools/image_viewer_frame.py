# https://www.geeksforgeeks.org/image-viewer-app-in-python-using-tkinter/

# Open files: config.json, insta_tags.db
# Read config['images_basedir'] and read JPG images in the directory
# tag and save to insta_tags.db

# importing the tkinter module and PIL that
# is pillow module
import tkinter as tk
#from tkinter.scrolledtext import ScrolledText
from scrolled_text_w_callback import ScrolledText
from PIL import ImageTk, Image


import json
from collections import OrderedDict

import sqlite3
import glob
import os

class ImageViewer():
    def __init__(self, root_window):
        # Calling the Tk (The intial constructor of tkinter)
        self.root = root_window


        # The geometry of the box which will be displayed
        # on the screen
        self.root.geometry("700x700")
        self.fr_buttons = tk.Frame(self.root, relief=tk.RAISED, bd=2)
        self.fr_buttons.pack(side=tk.LEFT, fill=tk.Y)


        self.chk_show_uploaded_val = tk.IntVar(value=1)
        self.chk_show_uploaded = tk.Checkbutton(self.fr_buttons, text='show uploaded', variable=self.chk_show_uploaded_val, command=self._on_show_tagged_untagged)
        self.chk_show_not_uploaded_val = tk.IntVar(value=1)
        self.chk_show_not_uploaded = tk.Checkbutton(self.fr_buttons, text='show not uploaded', variable=self.chk_show_not_uploaded_val, command=self._on_show_tagged_untagged)
        self.chk_show_untagged_val = tk.IntVar(value=1)
        self.chk_show_untagged = tk.Checkbutton(self.fr_buttons, text='show untagged', variable=self.chk_show_untagged_val, command=self._on_show_tagged_untagged)
        self.btn_last_edited = tk.Button(self.fr_buttons, text="Move to last edited", command=self._on_click_last_edited)

        self.btn_upload_insta = tk.Button(self.fr_buttons, text="Upload to Instagram", command=self._on_click_upload_insta)

        # root.quit for closing the app
        self.btn_exit = tk.Button(self.fr_buttons, text="Exit",
                             command=self.root.quit)
        # We will have three button back ,forward and exit
        self.btn_back = tk.Button(self.fr_buttons, text="< Back", command=self.back,
                             state=tk.DISABLED)
        self.txt_description = ScrolledText(self.fr_buttons, width=50, height=5, )


        self.config = json.load(open('config.json', 'r'), object_pairs_hook=OrderedDict)
        self.hashtag_groups = self.config['hashtag_groups']
        self.images_basedir = self.config['images_basedir']
        self.hashtag_group_chkbtns = []
        self.hashtag_group_chkbtn_vals = []

        for idx, (key, val) in enumerate(self.hashtag_groups.items()):
            self.hashtag_group_chkbtn_vals.append(tk.IntVar())
            # when using lambda, use default parameter idx=idx to avoid late-binding issue (otherwise `idx` is bound when the function is called)
            self.hashtag_group_chkbtns.append(tk.Checkbutton(self.fr_buttons, text=key, variable=self.hashtag_group_chkbtn_vals[idx], command=lambda idx=idx: self._hashtag_group_chkbtn_press(idx)))
            self.hashtag_group_chkbtns[idx].bind('<ButtonPress>', self._on_button_press)

        self.label_ratio = tk.Label(self.fr_buttons,text='crop ratio')
        self.radio_ratio_val = tk.IntVar()
        self.radio_ratio_none = tk.Radiobutton(self.fr_buttons, text="None", value=0, variable=self.radio_ratio_val, command=self._on_ratio)
        self.radio_ratio_45 = tk.Radiobutton(self.fr_buttons, text="4:5", value=1, variable=self.radio_ratio_val, command=self._on_ratio)
        self.radio_ratio_11 = tk.Radiobutton(self.fr_buttons, text="1:1", value=2, variable=self.radio_ratio_val, command=self._on_ratio)
        self.chk_crop_preview_val = tk.IntVar()
        self.chk_crop_preview= tk.Checkbutton(self.fr_buttons, text='crop preview', variable=self.chk_crop_preview_val, command=self._on_click_crop_preview)
        self.label_crop_x = tk.Label(self.fr_buttons,text='x')
        self.label_crop_y = tk.Label(self.fr_buttons,text='y')
        self.label_crop_size = tk.Label(self.fr_buttons,text='size')
        self.spin_crop_x_val = tk.StringVar(value='0.0')
        self.spin_crop_x = tk.Spinbox(self.fr_buttons,from_=-1.0, to=1.0, format='%.2f', increment=0.1, textvariable=self.spin_crop_x_val, justify=tk.CENTER)
        self.spin_crop_y_val = tk.StringVar(value='0.0')
        self.spin_crop_y = tk.Spinbox(self.fr_buttons,from_=-1.0, to=1.0, format='%.2f', increment=0.1, textvariable=self.spin_crop_y_val, justify=tk.CENTER)
        self.spin_crop_size_val = tk.StringVar(value='1.0')
        self.spin_crop_size = tk.Spinbox(self.fr_buttons,from_=0.0, to=2.0, format='%.2f', increment=0.1, textvariable=self.spin_crop_size_val, justify=tk.CENTER)
        self.btn_forward = tk.Button(self.fr_buttons, text="Forward >",
                                command=self.forward)
        self.label_description_preview_val = tk.StringVar()
        self.label_description_preview = tk.Label(self.fr_buttons, textvariable=self.label_description_preview_val, anchor='w', justify=tk.LEFT)

        self.fr_btn_widgets = []    # list of all the widgets in the left frame (in order), for grid (partially) and for binding click focus
        self.fr_btn_widgets.append(self.chk_show_uploaded)
        self.fr_btn_widgets.append(self.chk_show_not_uploaded)
        self.fr_btn_widgets.append(self.chk_show_untagged)
        self.fr_btn_widgets.append(self.btn_last_edited)
        self.fr_btn_widgets.append(self.btn_upload_insta)
        self.fr_btn_widgets.append(self.btn_exit)
        self.fr_btn_widgets.append(self.btn_back)
        self.fr_btn_widgets.append(self.txt_description)
        self.fr_btn_widgets.extend(self.hashtag_group_chkbtns)
        #self.fr_btn_widgets.append(self.label_ratio)
        self.fr_btn_widgets.append(self.radio_ratio_none)
        self.fr_btn_widgets.append(self.radio_ratio_45)
        self.fr_btn_widgets.append(self.radio_ratio_11)
        self.fr_btn_widgets.append(self.btn_forward)


        # row_widget
        row_widget = 0

        for widget in self.fr_btn_widgets[:8]:
            widget.grid(row=row_widget, column=0, columnspan=3, sticky="ew")
            row_widget += 1
        for widget in self.hashtag_group_chkbtns:
            widget.grid(row=row_widget, column=0, columnspan=3, sticky="ew")
            row_widget += 1

        self.label_ratio.grid(row=row_widget, column=0, columnspan=3, sticky="ew", pady=5)
        row_widget += 1
        self.radio_ratio_none.grid(row=row_widget, column=0, sticky="ew")
        self.radio_ratio_45.grid(row=row_widget, column=1, sticky="ew")
        self.radio_ratio_11.grid(row=row_widget, column=2, sticky="ew")
        row_widget += 1
        self.label_crop_x.grid(row=row_widget, column=0, sticky="ew")
        self.label_crop_y.grid(row=row_widget, column=1, sticky="ew")
        self.label_crop_size.grid(row=row_widget, column=2, sticky="ew")
        row_widget += 1
        self.spin_crop_x.grid(row=row_widget, column=0, sticky="ew", padx=15)
        self.spin_crop_y.grid(row=row_widget, column=1, sticky="ew", padx=15)
        self.spin_crop_size.grid(row=row_widget, column=2, sticky="ew", padx=15)
        row_widget += 1
        self.chk_crop_preview.grid(row=row_widget, column=0, columnspan=3, sticky="ew")
        row_widget += 1
        self.btn_forward.grid(row=row_widget, column=0, columnspan=3, sticky="ew")
        row_widget += 1
        self.label_description_preview.grid(row=row_widget, column=0, columnspan=3, sticky="w")


        #self.fr_buttons.grid(row=0, column=0, sticky="ns")
        #root.grid(row=0, column=1, sticky="nsew")

        self._read_image_list(self.images_basedir)
        self.label = tk.Label()
        self.canvas = tk.Canvas(self.root, width=300, height=200)#, bg="white")
        #self.canvas.grid(row=0, column=1, columnspan=3)
        self.canvas.pack(expand=tk.YES, fill=tk.BOTH)
        self.img_idx = 0
        self._change_image()

        # We have to show the the box so this below line is needed
        #self.label.grid(row=0, column=1, columnspan=3)

        self._key_bind()

        self._sqlite_connect()
        self._sqlite_create_table()


    def __del__(self):
        self._sqlite_close()

    def _read_image_list(self, basedir):
        files = os.listdir(basedir)
        self.image_basename_list = sorted([f for f in files if os.path.isfile(f) and f.lower().endswith('jpg')])
        #print(image_basename_list)

    def _update_description_preview(self):
        text = self.txt_description.get('1.0', tk.END).strip()
        # TODO add canon, hashtag groups
        self.label_description_preview_val.set(text)


    def _save_txt_description(self):
        '''Save when modification is detected only
        '''
        self._update_description_preview()
        text = self.txt_description.get('1.0', tk.END).strip()
        print(text)
        is_modified = self.txt_description.edit_modified()
        print(is_modified)

        # reset the flag
        self.txt_description.edit_modified(False)

    def _sqlite_connect(self):
        self.sqlite_conn = sqlite3.connect('insta_tags.db')
        self.sqlite_cursor = self.sqlite_conn.cursor()

    def _sqlite_create_table(self):
        self.sqlite_cursor.execute('''CREATE TABLE IF NOT EXISTS insta_tags (
        id INTEGER PRIMARY KEY,
        file_basename TEXT,
        description TEXT,
        hashtag_groups TEXT,
        width INTEGER,
        height INTEGER,
        crop_ratio TEXT,
        crop_size REAL,
        crop_x_offset REAL,
        crop_y_offset REAL,
        is_insta_uploaded INTEGER,
        last_updated TEXT )''')

    def _sqlite_close(self):
        self.sqlite_conn.close()

    def _key_bind(self):
        self.root.bind('<Left>', self._back_event)
        self.root.bind('<Right>', self._forward_event)
        self.root.protocol("WM_DELETE_WINDOW", self._on_close)
        self.root.bind('<Configure>', self._on_change_window_size)

        # unbind tab function for the text widget
        self.txt_description.bind('<Tab>', self._focus_next_widget)
        self.txt_description.bind('<FocusOut>', self._on_focus_out)
        self.txt_description.bind('<<TextModified>>', self._on_txt_modified)

        # move focus when pressing widgets
        self.root.bind('<ButtonPress>', self._on_button_press)

        for widget in self.fr_btn_widgets:
            widget.bind('<ButtonPress>', self._on_button_press)
#        self.chk_show_tagged.
#        self.chk_show_untagged.bind('<ButtonPress>', self._on_button_press)
#        self.btn_last_edited.bind('<ButtonPress>', self._on_button_press)
#        self.btn_upload_insta.bind('<ButtonPress>', self._on_button_press)
#        self.btn_exit.bind('<ButtonPress>', self._on_button_press)
#        self.btn_back.bind('<ButtonPress>', self._on_button_press)
#        self.btn_forward.bind('<ButtonPress>', self._on_button_press)

    def _forward_event(self, event):
        self.forward()
    def _back_event(self, event):
        self.back()

    def _hashtag_group_chkbtn_press(self, idx):
        print(idx)
        print(self.hashtag_group_chkbtn_vals[idx].get())

    def _focus_next_widget(self, event):
        '''To unbind tab key on the text widget
        '''
        event.widget.tk_focusNext().focus()
        return("break")

    def _on_show_tagged_untagged(self):
        if self.chk_show_uploaded_val.get() == 0 and self.chk_show_not_uploaded_val.get() == 0:
            self.btn_last_edited['state'] = tk.DISABLED
        else:
            self.btn_last_edited['state'] = tk.NORMAL

    def _on_click_last_edited(self):
        pass

    def _on_click_upload_insta(self):
        pass

    def _on_close(self):
        self._save_txt_description()
        self.root.destroy()

    def _on_focus_out(self, event):
        '''Save the description when the text box is out of focus
        '''
        if event.widget == self.txt_description:
            print('txt focus out')
            self._save_txt_description()

    def _on_txt_modified(self, event):
        '''Update preview as soon as description is modified
        '''
        if event.widget == self.txt_description:
            self._update_description_preview()

    def _on_button_press(self, event):
        '''Move focus
        '''
        event.widget.focus()

    def _on_ratio(self):
        pass

    def _refresh_canvas(self):
        #self.canvas.create_image(0,0,image=self.current_image, anchor=tk.NW)
        
        self.canvas.delete(tk.ALL)
        #self.canvas.create_image(0,0,image=self.current_image, anchor=tk.CENTER)
        self.canvas.create_image(self.canvas.winfo_width()/2,self.canvas.winfo_height()/2,image=self.current_image, anchor=tk.CENTER)
        self.canvas.create_rectangle(10*self.img_idx,10,100,100, dash=(3,3), outline="blue", width=2)
        #self.label.image = ImageTk.PhotoImage(Image.open(image_path))
        #self.label.configure(image=self.label.image)

    def _on_change_window_size(self, event):
        # refresh 
        self._refresh_canvas()

    def _on_click_crop_preview(self):
        # refresh 
        self._refresh_canvas()

    def _change_image(self):
        image_name = self.image_basename_list[self.img_idx]
        image_path = os.path.join(self.images_basedir, image_name)

        self.current_image = ImageTk.PhotoImage(Image.open(image_path))

        self._refresh_canvas()

        self.root.title("({:d}/{:d}) {:s}".format(self.img_idx+1, self.image_count(), image_name))

    def image_count(self):
        return len(self.image_basename_list)

    def forward(self):
        if self.img_idx == self.image_count() -1:
            return

        self._save_txt_description()

        self.img_idx += 1

        self._change_image()

        if self.img_idx == self.image_count() -1:
            self.btn_forward['state'] = tk.DISABLED

        if self.img_idx == 1:
            self.btn_back['state'] = tk.NORMAL

        self.txt_description.focus()


    def back(self):
        if self.img_idx == 0:
            return

        self._save_txt_description()

        self.img_idx -= 1

        self._change_image()

        if self.img_idx == self.image_count() -2:
            self.btn_forward['state'] = tk.NORMAL

        if self.img_idx == 0:
            self.btn_back['state'] = tk.DISABLED

        self.txt_description.focus()




if __name__ == '__main__':
    root = tk.Tk()
    ImageViewer(root)
    root.mainloop()
