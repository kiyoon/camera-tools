#/usr/bin/env python3
# Read SRT subtitles and convert them into the YouTube Chapters.

# default packages
import tkinter as tk
from tkinter import filedialog, ttk, messagebox
from tkinter.scrolledtext import ScrolledText

import json
from collections import OrderedDict

import glob
import os

SCRIPT_DIRPATH = os.path.dirname(os.path.realpath(__file__))

import sys
import copy
import logging

# needs to be installed 
import srt

# packages in current dir
import srt_utils

logger = logging.getLogger(__name__)    # add logger.success


class SrtToYTChapters():

    def __init__(self, root_window):
        self.srt_path = ''

        # Calling the Tk (The intial constructor of tkinter)
        self.root = root_window


        # The geometry of the box which will be displayed
        # on the screen
        self.root.geometry("420x500")
        self.root.title("SRT to YouTube Chapters")
        self.root.resizable(False, False)
        self.btn_open_srt = tk.Button(self.root, text="Open SRT", command=self._on_click_open_srt)
        self.label_offset_hour = tk.Label(self.root,text='offset (hour)')
        self.spin_offset_hour_val = tk.StringVar(value="0")
        self.spin_offset_hour = tk.Spinbox(self.root,from_=0, to=10, textvariable=self.spin_offset_hour_val, justify=tk.CENTER, state='readonly')
        self.label_fps = tk.Label(self.root,text='framerate (drift fix)')
        self.combo_fps_values=['Others (no fix)', '23.976', '29.97 NDF', '59.94 NDF'] 
        self.combo_fps_val = tk.StringVar(value=self.combo_fps_values[0])
        self.combo_fps=ttk.Combobox(self.root, state='readonly', values=self.combo_fps_values, textvariable=self.combo_fps_val)

        self.txt_youtube_chapters = ScrolledText(self.root, width=50, height=20, state=tk.DISABLED)

        self.btn_save_srt = tk.Button(self.root, text="Save SRT (optional: apply sync fix to SRT)", command=self._on_click_save_srt)

        row_widget = 0
        self.btn_open_srt.grid(row=row_widget, column=0, columnspan=1, sticky="ew", pady=10)
        row_widget += 1
        self.label_offset_hour.grid(row=row_widget, column=0, columnspan=1, sticky="ew", pady=10)
        self.spin_offset_hour.grid(row=row_widget, column=1, columnspan=2, sticky="ew", pady=10, padx=5)
        row_widget += 1
        self.label_fps.grid(row=row_widget, column=0, columnspan=1, sticky="ew", pady=10)
        self.combo_fps.grid(row=row_widget, column=1, columnspan=2, sticky="ew", pady=10, padx=5)

        row_widget += 1
        self.txt_youtube_chapters.grid(row=row_widget, column=0, columnspan=3, sticky="ew")
        row_widget += 1
        self.btn_save_srt.grid(row=row_widget, column=0, columnspan=3, sticky="ew", pady=10, padx=10)


        self.fr_btn_widgets = []    # list of all the widgets in the left frame (in order), for grid (partially) and for binding click focus
        self.fr_btn_widgets.append(self.btn_open_srt)
        self.fr_btn_widgets.append(self.spin_offset_hour)
        self.fr_btn_widgets.append(self.combo_fps)
        self.fr_btn_widgets.append(self.txt_youtube_chapters)
        self.fr_btn_widgets.append(self.btn_save_srt)

        # trace value changes
        self.spin_offset_hour_val.trace_add('write', self._on_offset_fps_change)
        self.combo_fps_val.trace_add('write', self._on_offset_fps_change)

        # open config file
        config_path = os.path.join(SCRIPT_DIRPATH, 'srt_to_youtube_chapters_config.json')
        try:
            with open(config_path, 'r', encoding='utf8') as f:
                config = json.load(f, object_pairs_hook=OrderedDict)
            # you don't want to erase the data yet. so mode 'a'
            self.config_file = open(config_path, 'a', encoding='utf8')
        except (FileNotFoundError, json.decoder.JSONDecodeError) as e:
            logger.info('Creating new config file')
            config = self.config_default()
            self.config_file = open(config_path, 'w', encoding='utf8')
            json.dump(config, self.config_file, indent=4, sort_keys=True)
            self.config_file.flush()

        self.config_to_values(config)

        self._key_bind()
        self._on_click_open_srt()

    def __del__(self):
        self.config_file.close()


    def config_default(self):
        config = {'last_open_dir': '/',
                'offset_hour': 0,
                'fps': self.combo_fps_values[0]}
        return config
    
    def config_to_values(self, config):
        self.last_open_dir = config['last_open_dir']
        self.spin_offset_hour_val.set(config['offset_hour'])
        self.combo_fps_val.set(config['fps'])
        
    def values_to_config(self):
        config = {'last_open_dir': self.last_open_dir,
                'offset_hour': int(self.spin_offset_hour_val.get()),
                'fps': self.combo_fps_val.get()}
        return config
    
    def save_config(self):
        config = self.values_to_config()
        self.config_file.truncate(0)    # erase
        json.dump(config, self.config_file, indent=4, sort_keys=True)   # write
        self.config_file.flush()    # apply changes 

    def update_readonly_txt(self, txt_widget, text):
        txt_widget['state'] = tk.NORMAL
        txt_widget.delete(1.0,tk.END)
        txt_widget.insert(tk.END,text)
        txt_widget['state'] = tk.DISABLED


    def _key_bind(self):
        self.root.protocol("WM_DELETE_WINDOW", self._on_close)

        # move focus when pressing widgets
        self.root.bind('<ButtonPress>', self._on_button_press)

        for widget in self.fr_btn_widgets:
            widget.bind('<ButtonPress>', self._on_button_press)


    def apply_srt_offset_multiplier(self):
        srt_lines = copy.deepcopy(self.srt_lines)
        offset_hour = int(self.spin_offset_hour_val.get())
        multiplier = 1 if self.combo_fps_val.get() == self.combo_fps_values[0] else 1001/1000
        srt_utils.srt_drift_fix_NTSC(srt_lines, offset_hour=offset_hour, multiplier=multiplier)
        return srt_lines

    def update_youtube_chapters(self):
        srt_lines = self.apply_srt_offset_multiplier()
        youtube_chapters = srt_utils.srt_to_youtube_chapters(srt_lines)
        self.update_readonly_txt(self.txt_youtube_chapters, youtube_chapters)

    def _on_click_open_srt(self):
        srt_path = filedialog.askopenfilename(initialdir=self.last_open_dir, title="Select file",
                                          filetypes=(("SRT subtitles", "*.srt"),
                                          ("all files", "*.*")))

        if srt_path != '':
            self.srt_path = srt_path
            self.last_open_dir = os.path.dirname(srt_path)
            self.save_config()
            self.root.title("SRT to YouTube Chapters - " + os.path.basename(self.srt_path))
            
            with open(self.srt_path, 'r', encoding="utf8") as f:
                self.srt_lines = list(srt.parse(f))

            self.update_youtube_chapters()
        else:
            if self.srt_path == '':
                # nothing opened, but the filedialog is closed too.
                # just shut down the programme.
                self.root.destroy()



    def _on_click_save_srt(self):
        try:
            srt_lines = self.apply_srt_offset_multiplier()
            with open(self.srt_path, 'w', encoding="utf8") as f:
                f.write(srt.compose(srt_lines))
        except Exception:
            messagebox.showinfo("Error", "An exception has occurred.")
        else:
            messagebox.showinfo("Save to SRT", "The offset and drift fix have successfully been saved to the opened SRT.")

    def _on_close(self):
        self.config_file.close()
        self.root.destroy()

    def _on_button_press(self, event):
        '''Move focus
        '''
        event.widget.focus()

    def _on_offset_fps_change(self, var, indx, mode):
        if self.srt_path != '':
            self.update_youtube_chapters()
            self.save_config()


if __name__ == '__main__':
    logging.basicConfig(stream=sys.stdout, level=logging.INFO,
            format='%(name)s: %(lineno)4d - %(levelname)s - %(message)s')
    try:
        # main
        root = tk.Tk()
        SrtToYTChapters(root)
        root.mainloop()
    except Exception:
        logger.exception("Exception occurred")
