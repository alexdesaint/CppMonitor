#!/usr/bin/python3
# -*- coding: utf-8 -*-

from tkinter import *
import io
import subprocess


def main():
    process = subprocess.Popen(["cmake"], stdout=subprocess.PIPE, stderr=subprocess.PIPE)

    out, outerr = process.communicate()

    root = Tk()
    text = Text(root)
    text.insert(END, out.decode('latin1'))
    text.insert(END, outerr.decode('latin1'))
    text.pack()

    text.tag_add("here", "1.0", "1.4")
    text.tag_add("start", "1.8", "1.13")
    text.tag_config("here", background="yellow", foreground="blue")
    text.tag_config("start", background="black", foreground="green")
    root.mainloop()

if __name__ == '__main__':
    main()