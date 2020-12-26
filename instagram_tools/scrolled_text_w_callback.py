# https://stackoverflow.com/questions/40617515/python-tkinter-text-modified-callback
# ScrolledText widget with <<TextModified>> event
import tkinter as tk
from tkinter.scrolledtext import ScrolledText as ST


class ScrolledText(ST):
    def __init__(self, *args, **kwargs):
        """A text widget that report on internal widget commands"""
        ST.__init__(self, *args, **kwargs)

        # create a proxy for the underlying widget
        self._orig = self._w + "_orig"
        self.tk.call("rename", self._w, self._orig)
        self.tk.createcommand(self._w, self._proxy)

    def _proxy(self, command, *args):
        cmd = (self._orig, command) + args
        result = self.tk.call(cmd)

        if command in ("insert", "delete", "replace"):
            self.event_generate("<<TextModified>>")

        return result
