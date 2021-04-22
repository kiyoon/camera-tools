# https://www.geeksforgeeks.org/image-viewer-app-in-python-using-tkinter/

# Open files: config.json, insta_tags.db
# Read config['images_basedir'] and read JPG images in the directory
# tag and save to insta_tags.db

# importing the tkinter module and PIL that
# is pillow module
import tkinter as tk
#from tkinter.scrolledtext import ScrolledText
from scrolled_text_w_callback import ScrolledText
from PIL import ImageTk, Image, ImageOps


import json
from collections import OrderedDict

import sqlite3
import glob
import os
from datetime import datetime

from instabot import Bot
import configparser
import random

SCRIPT_DIRPATH = os.path.dirname(os.path.realpath(__file__))

import sys
sys.path.append('..')
import exiftool
from utils.burn_signature import watermark_signature
from utils.pil_transpose import exif_transpose_delete_exif



import coloredlogs, logging, verboselogs
logger = verboselogs.VerboseLogger(__name__)    # add logger.success


RATIO_NONE = 0
RATIO_45 = 1
RATIO_11 = 2
RATIO_CUSTOM = 3

SQL_FILE_RELPATH = 0
SQL_DESCRIPTION = 1
SQL_HASHTAG_GROUPS = 2
SQL_CROP_RATIO = 3
SQL_CROP_SIZE = 4
SQL_CROP_X_OFFSET = 5
SQL_CROP_Y_OFFSET = 6
SQL_IS_INSTA_UPLOADED = 7
SQL_LAST_UPLOADED_UTC = 8

SQL_SEPARATOR = ';'

class ImageViewer():

    def __init__(self, root_window, insta_id = None, insta_password = None):
        if insta_id is not None:
            self.insta_bot = Bot()
            self.insta_bot.login(username=insta_id, password=insta_password)

        self.camera_info = ''
        self.camera_hashtags = ''

        self.current_image_pil = None
        self.current_image_proxy_pil = None
        self.proxy_file_exists = None

        # Calling the Tk (The intial constructor of tkinter)
        self.root = root_window


        # The geometry of the box which will be displayed
        # on the screen
        self.root.geometry("1400x1000")
        self.fr_buttons = tk.Frame(self.root, relief=tk.RAISED, bd=2)
        self.fr_buttons.pack(side=tk.LEFT, fill=tk.Y)

        self.sld_scale_var = tk.DoubleVar(value=1.0)
        self.sld_scale = tk.Scale(self.fr_buttons, from_ = 0.0, to = 4.0, resolution=0.1, orient=tk.HORIZONTAL, variable=self.sld_scale_var, command=self._scale_update)

        self.chk_show_uploaded_val = tk.IntVar(value=1)
        self.chk_show_uploaded = tk.Checkbutton(self.fr_buttons, text='show uploaded', variable=self.chk_show_uploaded_val, command=self._on_show_tagged_untagged)
        self.chk_show_not_uploaded_val = tk.IntVar(value=1)
        self.chk_show_not_uploaded = tk.Checkbutton(self.fr_buttons, text='show not uploaded', variable=self.chk_show_not_uploaded_val, command=self._on_show_tagged_untagged)
        self.chk_show_untagged_val = tk.IntVar(value=1)
        self.chk_show_untagged = tk.Checkbutton(self.fr_buttons, text='show untagged', variable=self.chk_show_untagged_val, command=self._on_show_tagged_untagged)
        self.chk_use_proxy_val = tk.IntVar(value=1)
        self.chk_use_proxy = tk.Checkbutton(self.fr_buttons, text='Use proxy if available', variable=self.chk_use_proxy_val, command=self._on_use_proxy)
        self.btn_last_edited = tk.Button(self.fr_buttons, text="Move to last edited", command=self._on_click_last_edited)

        self.btn_upload_insta = tk.Button(self.fr_buttons, text="Upload to Instagram", command=self._on_click_upload_insta)

        # root.quit for closing the app
        self.btn_exit = tk.Button(self.fr_buttons, text="Exit",
                             command=self.root.quit)
        # We will have three button back ,forward and exit
        self.btn_fast_back = tk.Button(self.fr_buttons, text="<< Fast Backward", command=self.fast_back, state=tk.DISABLED)
        self.btn_back = tk.Button(self.fr_buttons, text="< Back", command=self.back,
                             state=tk.DISABLED)
        self.txt_description = ScrolledText(self.fr_buttons, width=50, height=5, )


        self.config = json.load(open(os.path.join(SCRIPT_DIRPATH, 'config.json'), 'r', encoding='utf8'), object_pairs_hook=OrderedDict)
        self.hashtag_groups = self.config['hashtag_groups']
        self.hashtag_groups_indices = {k:i for i,k in enumerate(self.hashtag_groups.keys())}
        self.images_basedir = self.config['images_basedir']
        self.images_proxydir = self.config['images_proxydir']
        self.images_outputdir = self.config['images_outputdir']
        self.hashtag_group_chkbtns = []
        self.hashtag_group_chkbtn_vals = []

        for idx, (key, val) in enumerate(self.hashtag_groups.items()):
            self.hashtag_group_chkbtn_vals.append(tk.IntVar())
            # when using lambda, use default parameter idx=idx to avoid late-binding issue (otherwise `idx` is bound when the function is called)
            self.hashtag_group_chkbtns.append(tk.Checkbutton(self.fr_buttons, text=key, variable=self.hashtag_group_chkbtn_vals[idx], command=lambda idx=idx: self._hashtag_group_chkbtn_press(idx)))
            self.hashtag_group_chkbtns[idx].bind('<ButtonPress>', self._on_button_press)

        self.label_ratio = tk.Label(self.fr_buttons,text='crop ratio')
        self.radio_ratio_val = tk.IntVar()
        self.radio_ratio_none = tk.Radiobutton(self.fr_buttons, text="None", value=RATIO_NONE, variable=self.radio_ratio_val, command=self._on_ratio)
        self.radio_ratio_45 = tk.Radiobutton(self.fr_buttons, text="4:5", value=RATIO_45, variable=self.radio_ratio_val, command=self._on_ratio)
        self.radio_ratio_11 = tk.Radiobutton(self.fr_buttons, text="1:1", value=RATIO_11, variable=self.radio_ratio_val, command=self._on_ratio)
        self.radio_ratio_custom = tk.Radiobutton(self.fr_buttons, text="Custom", value=RATIO_CUSTOM, variable=self.radio_ratio_val, command=self._on_ratio)
        self.spin_ratio_x_val = tk.StringVar(value="3")
        self.spin_ratio_x = tk.Spinbox(self.fr_buttons,from_=1, to=30, textvariable=self.spin_ratio_x_val, justify=tk.CENTER)
        self.spin_ratio_y_val = tk.StringVar(value="2")
        self.spin_ratio_y = tk.Spinbox(self.fr_buttons,from_=1, to=30, textvariable=self.spin_ratio_y_val, justify=tk.CENTER)
        self.label_ratio_custom = tk.Label(self.fr_buttons,text=':')

        self.label_crop_x = tk.Label(self.fr_buttons,text='x')
        self.label_crop_y = tk.Label(self.fr_buttons,text='y')
        self.label_crop_size = tk.Label(self.fr_buttons,text='size')
        self.spin_crop_x_val = tk.StringVar(value='0.0')
        self.spin_crop_x = tk.Spinbox(self.fr_buttons,from_=-1.0, to=1.0, format='%.2f', increment=0.02, textvariable=self.spin_crop_x_val, justify=tk.CENTER)
        self.spin_crop_y_val = tk.StringVar(value='0.0')
        self.spin_crop_y = tk.Spinbox(self.fr_buttons,from_=-1.0, to=1.0, format='%.2f', increment=0.02, textvariable=self.spin_crop_y_val, justify=tk.CENTER)
        self.spin_crop_size_val = tk.StringVar(value='1.0')
        self.spin_crop_size = tk.Spinbox(self.fr_buttons,from_=0.0, to=2.0, format='%.2f', increment=0.02, textvariable=self.spin_crop_size_val, justify=tk.CENTER)

        # trace value changes
        self.spin_crop_x_val.trace_add('write', self._on_crop_xysize)
        self.spin_crop_y_val.trace_add('write', self._on_crop_xysize)
        self.spin_crop_size_val.trace_add('write', self._on_crop_xysize)

        self.chk_crop_preview_val = tk.IntVar()
        self.chk_crop_preview= tk.Checkbutton(self.fr_buttons, text='crop preview', variable=self.chk_crop_preview_val, command=self._on_click_crop_preview)

        self.btn_forward = tk.Button(self.fr_buttons, text="Forward >",
                                command=self.forward)
        self.btn_fast_forward = tk.Button(self.fr_buttons, text="Fast Forward >>",
                                command=self.fast_forward)
        self.txt_description_preview = ScrolledText(self.fr_buttons, width=50, height=20, state=tk.DISABLED)

        self.chk_is_proxy_val = tk.IntVar()
        self.chk_is_proxy = tk.Checkbutton(self.fr_buttons, text='proxy', variable=self.chk_is_proxy_val, state=tk.DISABLED, anchor=tk.W)
        self.chk_is_uploaded_val = tk.IntVar()
        self.chk_is_uploaded = tk.Checkbutton(self.fr_buttons, text='instagram uploaded', variable=self.chk_is_uploaded_val, state=tk.DISABLED, anchor=tk.W)

        self.fr_btn_widgets = []    # list of all the widgets in the left frame (in order), for grid (partially) and for binding click focus
        self.fr_btn_widgets.append(self.sld_scale)
        self.fr_btn_widgets.append(self.chk_show_uploaded)
        self.fr_btn_widgets.append(self.chk_show_not_uploaded)
        self.fr_btn_widgets.append(self.chk_show_untagged)
        self.fr_btn_widgets.append(self.chk_use_proxy)
        self.fr_btn_widgets.append(self.btn_last_edited)
        self.fr_btn_widgets.append(self.btn_upload_insta)
        self.fr_btn_widgets.append(self.btn_exit)
        self.fr_btn_widgets.append(self.btn_fast_back)
        self.fr_btn_widgets.append(self.btn_back)
        self.fr_btn_widgets.append(self.txt_description)
        self.fr_btn_widgets.extend(self.hashtag_group_chkbtns)
        #self.fr_btn_widgets.append(self.label_ratio)
        self.fr_btn_widgets.append(self.radio_ratio_none)
        self.fr_btn_widgets.append(self.radio_ratio_45)
        self.fr_btn_widgets.append(self.radio_ratio_11)
        self.fr_btn_widgets.append(self.radio_ratio_custom)
        self.fr_btn_widgets.append(self.spin_ratio_x)
        self.fr_btn_widgets.append(self.spin_ratio_y)
        self.fr_btn_widgets.append(self.spin_crop_size)
        self.fr_btn_widgets.append(self.spin_crop_x)
        self.fr_btn_widgets.append(self.spin_crop_y)
        self.fr_btn_widgets.append(self.chk_crop_preview)
        self.fr_btn_widgets.append(self.btn_forward)
        self.fr_btn_widgets.append(self.btn_fast_forward)
        self.fr_btn_widgets.append(self.txt_description_preview)


        # row_widget
        row_widget = 0

        for widget in self.fr_btn_widgets[:11]:
            # until txt_description
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
        self.radio_ratio_custom.grid(row=row_widget, column=0, sticky="ew")
        self.spin_ratio_x.grid(row=row_widget, column=1, sticky="ew", padx=40)
        self.label_ratio_custom.grid(row=row_widget, column=1, sticky="ee")
        self.spin_ratio_y.grid(row=row_widget, column=2, sticky="ew",padx=40)
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
        self.btn_fast_forward.grid(row=row_widget, column=0, columnspan=3, sticky="ew")
        row_widget += 1
        self.txt_description_preview.grid(row=row_widget, column=0, columnspan=3, sticky="ew")
        row_widget += 1
        self.chk_is_proxy.grid(row=row_widget, column=0, columnspan=3, sticky="ew")
        row_widget += 1
        self.chk_is_uploaded.grid(row=row_widget, column=0, columnspan=3, sticky="ew")

        self._sqlite_connect()
        self._sqlite_create_table()

        #self.fr_buttons.grid(row=0, column=0, sticky="ns")
        #root.grid(row=0, column=1, sticky="nsew")

        self._read_image_list(self.images_basedir)
        self.label = tk.Label()
        self.canvas = tk.Canvas(self.root, width=300, height=200)#, bg="white")
        self.canvas.pack(expand=tk.YES, fill=tk.BOTH)
        self.img_idx = 0
        self._change_image()

        # We have to show the the box so this below line is needed
        #self.label.grid(row=0, column=1, columnspan=3)

        self._key_bind()



    def __del__(self):
        self._sqlite_close()
        self.insta_bot.logout()

    def _read_image_list(self, basedir: str):
        self.image_relpath_list = []
        for root, dirs, files in os.walk(basedir):
            reldir = root.replace(basedir, '')
            if reldir.startswith(os.sep):
                reldir = reldir[1:]
            self.image_relpath_list.extend(sorted([os.path.join(reldir,f).replace(os.sep, '/') for f in files if f.lower().endswith('jpg')]))

    def get_insta_description(self):
        text = self.txt_description.get('1.0', tk.END).strip()
        num_hashtags_desc = text.count('#')

        text += '\n\n' + self.camera_info + '\n\n'

        hashtags = ''
        for idx, (key, val) in enumerate(self.hashtag_groups.items()):
            if self.hashtag_group_chkbtn_vals[idx].get() == 1:
                hashtags += val
                hashtags += ' '

        hashtags += self.camera_hashtags
        num_hashtags = hashtags.count('#')

        if num_hashtags_desc + num_hashtags > 30:
            hashtags_list = hashtags.split(' ')
            random.shuffle(hashtags_list)
            hashtags_list = hashtags_list[:30-num_hashtags_desc]
            hashtags = ' '.join(hashtags_list)

        return text + hashtags

    def _update_description_preview(self):
        text = self.get_insta_description()
                
        self.txt_description_preview['state'] = tk.NORMAL
        self.txt_description_preview.delete(1.0,tk.END)
        self.txt_description_preview.insert(tk.END,text)
        self.txt_description_preview['state'] = tk.DISABLED


    def _save_txt_description(self):
        '''Save when modification is detected only
        '''
        #self._update_description_preview()
        text = self.txt_description.get('1.0', tk.END).strip()
        is_modified = self.txt_description.edit_modified()

        if is_modified:
            #self._sqlite_upsert_description(text)
            self._sqlite_upsert_one_field('description', text)

        # reset the flag
        self.txt_description.edit_modified(False)

    def _save_hashtag_groups(self):
        group_keys = []
        for idx, (key, val) in enumerate(self.hashtag_groups.items()):
            if self.hashtag_group_chkbtn_vals[idx].get() == 1:
                group_keys.append(key)
        
        self._sqlite_upsert_one_field('hashtag_groups', SQL_SEPARATOR.join(group_keys))
        
    def _save_crop_ratio(self):
        ratio_mode = self.radio_ratio_val.get()
        if ratio_mode == RATIO_NONE:
            text = 'none'
        elif ratio_mode == RATIO_45:
            text = '4:5'
        elif ratio_mode == RATIO_11:
            text = '1:1'
        else:
            text = self.spin_ratio_x_val.get() + ":" + self.spin_ratio_y_val.get()
        self._sqlite_upsert_one_field('crop_ratio', text)

    def _save_crop_x(self):
        x_offset = float(self.spin_crop_x_val.get())
        self._sqlite_upsert_one_field('crop_x_offset', x_offset)

    def _save_crop_y(self):
        y_offset = float(self.spin_crop_y_val.get())
        self._sqlite_upsert_one_field('crop_y_offset', y_offset)

    def _save_crop_size(self):
        crop_size = float(self.spin_crop_size_val.get())
        self._sqlite_upsert_one_field('crop_size', crop_size)

    def _sqlite_upsert_one_field(self, column, value):
        '''Updates the field with the current file path.
        Updates the last updated timestamp automatically.
        '''
        last_updated_ts = datetime.utcnow().timestamp()
        
        self.sqlite_cursor.execute(f'''INSERT INTO insta_tags(file_relpath, {column}, last_updated_utc)
        VALUES(?,?,?)
        ON CONFLICT(file_relpath) DO UPDATE SET
        {column}=excluded.{column},
        last_updated_utc=excluded.last_updated_utc;''', (self.image_relpath_list[self.img_idx], value, last_updated_ts))
        self.sqlite_conn.commit()

    def _sqlite_connect(self):
        self.sqlite_conn = sqlite3.connect(os.path.join(SCRIPT_DIRPATH, 'insta_tags.db'))
        self.sqlite_cursor = self.sqlite_conn.cursor()

    def _sqlite_create_table(self):
        self.sqlite_cursor.execute('''CREATE TABLE IF NOT EXISTS insta_tags (
        file_relpath TEXT PRIMARY KEY,
        description TEXT,
        hashtag_groups TEXT,
        crop_ratio TEXT DEFAULT none,
        crop_size REAL DEFAULT 1.0,
        crop_x_offset REAL DEFAULT 0.0,
        crop_y_offset REAL DEFAULT 0.0,
        is_insta_uploaded INTEGER DEFAULT 0,
        last_updated_utc REAL )''')

        self.sqlite_conn.commit()

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

        self.spin_crop_size.bind('<FocusOut>', self._on_focus_out)
        self.spin_crop_x.bind('<FocusOut>', self._on_focus_out)
        self.spin_crop_y.bind('<FocusOut>', self._on_focus_out)

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
        self._update_description_preview()
        self._save_hashtag_groups()

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

    def _on_use_proxy(self):
        if self.chk_use_proxy_val.get() == 0:
            self.chk_is_proxy_val.set(0)
        else:
            _, is_proxy = self.get_image()
            self.chk_is_proxy_val.set(is_proxy)
        self._scale_update()


    def _on_click_last_edited(self):
        pass

    def _on_click_upload_insta(self):
        # process image
        # 
        image = self.get_original_image()
        crop_xywh = self.get_crop_xywh(image)
        img = self.get_scaled_cropped_image(image, 1.0, crop_xywh, resample=Image.LANCZOS)
        img = watermark_signature(img).convert('RGB')

        output_filepath = os.path.join(self.images_outputdir, self.image_relpath_list[self.img_idx])
        output_dirpath = os.path.dirname(output_filepath)
        os.makedirs(output_dirpath, exist_ok=True)

        img.save(output_filepath, quality=95)
        logger.info('Image saved to %s', output_filepath)

        #caption = self.get_insta_description()
        caption = self.txt_description_preview.get('1.0', tk.END).strip()
        logger.info('Instagram caption: %s', caption)

        #self.insta_bot.upload_photo(output_filepath, caption)
        self.insta_bot.upload_photo(output_filepath, caption)
        os.rename(output_filepath + '.REMOVE_ME', output_filepath)

        self._sqlite_upsert_one_field('is_insta_uploaded', 1)
        self.chk_is_uploaded_val.set(1)

    def _on_close(self):
        self._save_txt_description()
        self._save_crop_size()
        self._save_crop_x()
        self._save_crop_y()
        self.root.destroy()

    def _on_focus_out(self, event):
        '''Save the description when the text box is out of focus
        '''
        if event.widget == self.txt_description:
            logger.info('Description text focus out: Saving..')
            self._save_txt_description()

        elif event.widget == self.spin_crop_size:
            logger.info('Crop size focus out: Saving..')
            self._save_crop_size()

        elif event.widget == self.spin_crop_x:
            logger.info('Crop x focus out: Saving..')
            self._save_crop_x()

        elif event.widget == self.spin_crop_y:
            logger.info('Crop y focus out: Saving..')
            self._save_crop_y()

    def _on_txt_modified(self, event):
        '''Update preview as soon as description is modified
        '''
        if event.widget == self.txt_description:
            self._update_description_preview()

    def _on_button_press(self, event):
        '''Move focus
        '''
        event.widget.focus()

    def _on_crop_xysize(self, var, indx, mode):
        if self.chk_crop_preview_val.get() == 1:
            self._scale_update()
        else:
            self._refresh_canvas()

    def _ratio_disability_update(self):
        ratio_mode = self.radio_ratio_val.get()
        if ratio_mode == RATIO_NONE:
            self.spin_crop_x['state'] = tk.DISABLED
            self.spin_crop_y['state'] = tk.DISABLED
            self.spin_crop_size['state'] = tk.DISABLED
            self.chk_crop_preview['state'] = tk.DISABLED
        else:
            self.spin_crop_x['state'] = tk.NORMAL
            self.spin_crop_y['state'] = tk.NORMAL
            self.spin_crop_size['state'] = tk.NORMAL
            self.chk_crop_preview['state'] = tk.NORMAL


        if ratio_mode == RATIO_CUSTOM:
            self.spin_ratio_x['state'] = tk.NORMAL
            self.spin_ratio_y['state'] = tk.NORMAL
        else:
            self.spin_ratio_x['state'] = tk.DISABLED
            self.spin_ratio_y['state'] = tk.DISABLED


    def _on_ratio(self):
        self._ratio_disability_update()

        if self.chk_crop_preview_val.get() == 1:
            self._scale_update()
        else:
            self._refresh_canvas()

        logger.info('Ratio changed: Saving..')
        self._save_crop_ratio()

    def point_to_canvas(self, image: Image.Image, x, y):
        '''Convert image point coordinate to canvas coordinate
        Considers scaling and canvas offset (image is centre aligned)
        '''
        canvas_width = self.canvas.winfo_width()
        canvas_height = self.canvas.winfo_height()
        image_width, image_height = image.size
        scale = self.sld_scale_var.get()
        # adding canvas offset
        canvas_x = x * scale + (canvas_width - image_width * scale)/2
        canvas_y = y * scale + (canvas_height - image_height * scale)/2

        if self.chk_crop_preview_val.get() == 1:
            # image centre - crop centre is the another offset
            crop_xywh = self.get_crop_xywh(image)
            crop_centre_x = crop_xywh[0] + crop_xywh[2]/2
            crop_centre_y = crop_xywh[1] + crop_xywh[3]/2
            canvas_x += (image_width/2 - crop_centre_x)*scale
            canvas_y += (image_height/2 - crop_centre_y)*scale

        return round(canvas_x), round(canvas_y)

    def rectangle_to_canvas(self, image: Image.Image, x, y, w, h):
        x1, y1, x2, y2 = self.xywh_to_xyxy(x, y, w, h)
        canvas_x1, canvas_y1 = self.point_to_canvas(image, x1,y1)
        canvas_x2, canvas_y2 = self.point_to_canvas(image, x2,y2)
        return canvas_x1, canvas_y1, canvas_x2, canvas_y2

    def get_crop_xywh(self, image: Image.Image):
        ratio_mode = self.radio_ratio_val.get()

        if ratio_mode == RATIO_NONE:
            return None
        else:
            if ratio_mode == RATIO_45:
                ratio_x = 4
                ratio_y = 5
            elif ratio_mode == RATIO_11:
                ratio_x = 1
                ratio_y = 1
            else:
                # RATIO_CUSTOM
                ratio_x = int(self.spin_ratio_x_val.get())
                ratio_y = int(self.spin_ratio_y_val.get())

            crop_x_offset = float(self.spin_crop_x_val.get())
            crop_y_offset = float(self.spin_crop_y_val.get())
            crop_size = float(self.spin_crop_size_val.get())

            crop_ratio = ratio_x / ratio_y
            image_width, image_height = image.size
            image_ratio = image_width / image_height

            if image_ratio > crop_ratio:
                # image is wider. crop_size==1 should be matching image's height.
                # base width and height when crop_size==1
                crop_base_height = image_height
                crop_base_width = crop_base_height / ratio_y * ratio_x
            else:
                # image is narrower. crop_size==1 should be matching image's width.
                # base width and height when crop_size==1
                crop_base_width = image_width
                crop_base_height = crop_base_width / ratio_x * ratio_y

            crop_centre_x = image_width / 2 + (crop_x_offset * image_width / 2)
            crop_centre_y = image_height / 2 + (crop_y_offset * image_height / 2)
            crop_width = crop_base_width * crop_size
            crop_height = crop_base_height * crop_size
            crop_x1 = crop_centre_x - (crop_width / 2)
            crop_y1 = crop_centre_y - (crop_height / 2)
            return crop_x1, crop_y1, crop_width, crop_height

    def xywh_to_xyxy(self, x, y, w, h):
        return x, y, x+w, y+h

    def get_scaled_cropped_image(self, image: Image.Image, scale, crop_xywh, resample=Image.BICUBIC):
        if crop_xywh is not None:
            new_image_size = tuple(map(lambda x: round(x*scale), crop_xywh[2:]))
            crop_xyxy = tuple(map(round, self.xywh_to_xyxy(*crop_xywh)))

            # perform padding when crop is out of border
            image_width, image_height = image.size
            padding = None
            if crop_xyxy[0] < 0:
                if padding is None:
                    padding = [0,0,0,0]
                padding[0] = -crop_xyxy[0]
            if crop_xyxy[1] < 0:
                if padding is None:
                    padding = [0,0,0,0]
                padding[1] = -crop_xyxy[1]
            if crop_xyxy[2] > image_width:
                if padding is None:
                    padding = [0,0,0,0]
                padding[2] = crop_xyxy[2] - image_width
            if crop_xyxy[3] > image_height:
                if padding is None:
                    padding = [0,0,0,0]
                padding[3] = crop_xyxy[3] - image_height

            if padding is None:
                current_image_pil_scaled = image.resize(new_image_size, box=crop_xyxy, resample=resample)
            else:
                logger.warning('white padding applied to the image borders')
                padding = tuple(padding)
                crop_xyxy_padded = (crop_xyxy[0] + padding[0], crop_xyxy[1] + padding[1],
                        crop_xyxy[2] + padding[0], crop_xyxy[3] + padding[1])   # padding on the left and top sides makes the box shift, but not the right and bottom sides.
                current_image_pil_scaled = ImageOps.expand(image, border=padding, fill=(255,255,255)).resize(new_image_size, box=crop_xyxy_padded, resample=resample)
        else:
            if scale == 1.0:
                # use the original and do not make a copy
                current_image_pil_scaled = image
            else:
                new_image_size = tuple(map(lambda x: round(x*scale), image.size))
                current_image_pil_scaled = image.resize(new_image_size, resample=resample)

        return current_image_pil_scaled


    def _scale_update(self, event=None):
        '''Manipulate original image
        1. Apply scaling
        2. Apply crop preview
        3. Apply proxy
        '''
        scale = self.sld_scale_var.get()

        image, use_proxy = self.get_image()
        crop_xywh = self.get_crop_xywh(image)
        
        if self.chk_crop_preview_val.get() == 1 and crop_xywh is not None:
            self.current_image_pil_scaled = self.get_scaled_cropped_image(image, scale, crop_xywh, resample=Image.BILINEAR)
        else:
            if scale == 1.0:
                # use the original and do not make a copy
                self.current_image_pil_scaled = image
            else:
                new_image_size = tuple(map(lambda x: round(x*scale), image.size))
                self.current_image_pil_scaled = image.resize(new_image_size, resample=Image.BILINEAR)

        self.current_image = ImageTk.PhotoImage(self.current_image_pil_scaled)
        self._refresh_canvas()

    def _refresh_canvas(self):
        '''DO NOT change the image itself but change the positioning
        '''
        #self.canvas.create_image(0,0,image=self.current_image, anchor=tk.NW)
        
        self.canvas.delete(tk.ALL)
        #self.canvas.create_image(0,0,image=self.current_image, anchor=tk.CENTER)
        canvas_width = self.canvas.winfo_width()
        canvas_height = self.canvas.winfo_height()
        self.canvas.create_image(canvas_width/2,canvas_height/2,image=self.current_image, anchor=tk.CENTER)
        #self.label.image = ImageTk.PhotoImage(Image.open(image_path))
        #self.label.configure(image=self.label.image)

        # crop
        image, use_proxy = self.get_image()
        crop_xywh = self.get_crop_xywh(image)
        if crop_xywh is not None:
            canvas_crop_xyxy = self.rectangle_to_canvas(image, *crop_xywh)

            is_crop_preview = self.chk_crop_preview_val.get()
            if is_crop_preview == 0:
                # draw rectangle
                self.canvas.create_rectangle(*canvas_crop_xyxy, dash=(3,3), outline="blue", width=2)

    def _on_change_window_size(self, event):
        # refresh 
        self._refresh_canvas()

    def _on_click_crop_preview(self):
        # refresh 
        self._scale_update()

    def get_original_image(self):
        if self.current_image_pil is None:
            image_path = os.path.join(self.images_basedir, self.image_relpath)

            self.current_image_pil, _, _ = exif_transpose_delete_exif(Image.open(image_path))
        return self.current_image_pil


    def get_image(self):
        '''
        Gets image (get proxy if user sets it and file available)
        Returns:
            image (PIL)
            is_proxy (bool)
        '''
        use_proxy = bool(self.chk_use_proxy_val.get())
        if use_proxy:
            if self.current_image_proxy_pil is None:
                if self.proxy_file_exists is None:
                    proxy_path = os.path.join(self.images_proxydir, self.image_relpath)

                    if os.path.isfile(proxy_path):
                        self.proxy_file_exists = True
                        self.current_image_proxy_pil, _, _ = exif_transpose_delete_exif(Image.open(proxy_path))
                        return self.current_image_proxy_pil, True
                    else:
                        self.proxy_file_exists = False
                        return self.get_original_image(), False
                elif not self.proxy_file_exists:
                    return self.get_original_image(), False
                else:
                    raise NotImplementedError()
            else:
                return self.current_image_proxy_pil, True

        else:
            return self.get_original_image(), False

        

    def _change_image(self):
        # This is a Linux path with / no matter what OS you use.
        self.image_relpath = self.image_relpath_list[self.img_idx]
        # This is an OS dependent path with / or \.
        image_path = os.path.join(self.images_basedir, self.image_relpath.replace('/', os.sep))
        self.current_image_pil = None
        self.current_image_proxy_pil = None
        self.proxy_file_exists = None
        #self.current_image_pil = Image.open(image_path)

        use_proxy = bool(self.chk_use_proxy_val.get())
        pil, is_proxy = self.get_image()
        self.chk_is_proxy_val.set(int(is_proxy))
        self.current_image = ImageTk.PhotoImage(pil)    # this is replaced by scaled image

        self._scale_update()

        self.root.title("({:d}/{:d}) {:s}".format(self.img_idx+1, self.image_count(), self.image_relpath))

        # read exif
        self.camera_info = ''
        self.camera_hashtags = ''
        try:
            with exiftool.ExifTool() as et:
                metadata = et.get_metadata(image_path)
        except json.decoder.JSONDecodeError:
            return

        for key, val in self.config['exif'].items():
            if 'exif_field' in val.keys():
                if val['exif_field'] in metadata.keys():
                    metavalue = str(metadata[val['exif_field']])

                    if 'format' in val.keys():
                        self.camera_info += val['format'].replace("%s", metavalue) + '\n'
                    if 'hashtag' in val.keys():
                        self.camera_hashtags += val['hashtag'].replace("%s", metavalue) + ' '
                    if 'hashtags' in val.keys():
                        if metavalue in val['hashtags'].keys():
                            self.camera_hashtags += val['hashtags'][metavalue] + ' '
                    if 'conditional_hashtags' in val.keys():
                        for condition in val['conditional_hashtags'].keys():
                            if eval(metavalue + condition):
                                self.camera_hashtags += val['conditional_hashtags'][condition] + ' '



            elif 'exif_fields' in val.keys():
                metavalues = []
                bypass_format = False
                for key2 in val['exif_fields']:
                    if key2 in metadata.keys():
                        metavalues.append(metadata[key2])
                    else:
                        logger.warning('%s not found in EXIF of file %s', key2, self.image_relpath)
                        bypass_format = True

                if not bypass_format and 'format' in val.keys():
                    formatted_str = val['format']
                    for i, metaval in enumerate(metavalues):
                        formatted_str = formatted_str.replace("%{:d}".format(i+1), str(metaval))
                    self.camera_info += formatted_str + '\n'
            else:
                raise ValueError()


        # check db
        self.sqlite_cursor.execute('SELECT * FROM insta_tags WHERE file_relpath=?', (self.image_relpath,))
        db_imageinfo = self.sqlite_cursor.fetchone()

        logger.info("Loaded info from DB: %s", str(db_imageinfo))
        self.initialise_widgets()
        if db_imageinfo is not None:
            if db_imageinfo[SQL_DESCRIPTION] is not None:
                self.txt_description.insert(tk.END,db_imageinfo[SQL_DESCRIPTION])


            if db_imageinfo[SQL_HASHTAG_GROUPS] is not None:
                for hashtag_group in db_imageinfo[SQL_HASHTAG_GROUPS].split(SQL_SEPARATOR):
                    idx = self.hashtag_groups_indices[hashtag_group]
                    self.hashtag_group_chkbtn_vals[idx].set(1)

            if db_imageinfo[SQL_CROP_RATIO] == 'none':
                self.radio_ratio_val.set(RATIO_NONE)
            elif db_imageinfo[SQL_CROP_RATIO] == '4:5':
                self.radio_ratio_val.set(RATIO_45)
            elif db_imageinfo[SQL_CROP_RATIO] == '1:1':
                self.radio_ratio_val.set(RATIO_11)
            else:
                ratio_xy = db_imageinfo[SQL_CROP_RATIO].split(':')
                if len(ratio_xy) != 2:
                    raise ValueError(f'Unknown ratio {db_imageinfo[SQL_CROP_RATIO]}')
                self.radio_ratio_val.set(RATIO_CUSTOM)
                self.spin_ratio_x_val.set(ratio_xy[0])
                self.spin_ratio_y_val.set(ratio_xy[1])

            self.spin_crop_size_val.set(db_imageinfo[SQL_CROP_SIZE])
            self.spin_crop_x_val.set(db_imageinfo[SQL_CROP_X_OFFSET])
            self.spin_crop_y_val.set(db_imageinfo[SQL_CROP_Y_OFFSET])
            self._ratio_disability_update()

            if db_imageinfo[SQL_IS_INSTA_UPLOADED] is not None:
                self.chk_is_uploaded_val.set(db_imageinfo[SQL_IS_INSTA_UPLOADED])
            else:
                self.chk_is_uploaded_val.set(0)

        self._update_description_preview()

        # reset the modified flag
        self.txt_description.edit_modified(False)

    def initialise_widgets(self):
        self.txt_description.delete(1.0,tk.END)
        # initialise hashtag groups (set to False)
        for hashtag_group_val in self.hashtag_group_chkbtn_vals:
            hashtag_group_val.set(0)
        self.radio_ratio_val.set(RATIO_NONE)
        self.spin_crop_size_val.set(1.0)
        self.spin_crop_x_val.set(0.0)
        self.spin_crop_y_val.set(0.0)
        self._ratio_disability_update()

    def image_count(self):
        return len(self.image_relpath_list)

    def _forward_back_disability_update(self, fast_count=20):
        if self.img_idx >= self.image_count() - 1:
            self.btn_forward['state'] = tk.DISABLED
        else:
            self.btn_forward['state'] = tk.NORMAL

        if self.img_idx >= self.image_count() - fast_count:
            self.btn_fast_forward['state'] = tk.DISABLED
        else:
            self.btn_fast_forward['state'] = tk.NORMAL

        if self.img_idx > 0:
            self.btn_back['state'] = tk.NORMAL
        else:
            self.btn_back['state'] = tk.DISABLED

        if self.img_idx > fast_count:
            self.btn_fast_back['state'] = tk.NORMAL
        else:
            self.btn_fast_back['state'] = tk.DISABLED

    def forward(self, count = 1):
        if self.img_idx >= self.image_count() - count:
            return

        self._save_txt_description()
        self._save_crop_size()
        self._save_crop_x()
        self._save_crop_y()

        self.img_idx += count

        self._change_image()

        self._forward_back_disability_update()

        self.txt_description.focus()


    def back(self, count = 1):
        if self.img_idx < count:
            return

        self._save_txt_description()
        self._save_crop_size()
        self._save_crop_x()
        self._save_crop_y()

        self.img_idx -= count

        self._change_image()

        self._forward_back_disability_update()

        self.txt_description.focus()

    def fast_forward(self):
        self.forward(20)

    def fast_back(self):
        self.back(20)




if __name__ == '__main__':
    coloredlogs.install(fmt='%(name)s: %(lineno)4d - %(levelname)s - %(message)s', level='INFO')
    try:
        # main
        config = configparser.ConfigParser()
        config.read('key.ini')
        insta_id = config['instagram']['id']
        insta_password = config['instagram']['password']

        root = tk.Tk()
        ImageViewer(root, insta_id, insta_password)
        root.mainloop()
    except Exception:
        logger.exception("Exception occurred")
