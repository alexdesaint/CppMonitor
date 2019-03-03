#!/usr/bin/python3
# -*- coding: utf-8 -*-

import sys
import subprocess
import logging
import re

from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *

class MainWindow(QWidget):
    def __init__(self):
        super().__init__(None, Qt.WindowStaysOnTopHint | Qt.FramelessWindowHint)

        self.btnGenerate = QPushButton('Generate', self)
        self.btnGenerate.move(0, 0)
        self.btnGenerate.resize(60, 20)
        self.btnGenerate.clicked.connect(self.generate)

        self.btnBuild = QPushButton('Build', self)
        self.btnBuild.move(60, 0)
        self.btnBuild.resize(60, 20)
        self.btnBuild.clicked.connect(self.build)

        self.btnClean = QPushButton('Clean', self)
        self.btnClean.move(60*2, 0)
        self.btnClean.resize(60, 20)
        self.btnClean.clicked.connect(self.clean)

        self.btnRun = QPushButton('Run', self)
        self.btnRun.move(60*3, 0)
        self.btnRun.resize(60, 20)
        self.btnRun.clicked.connect(self.run)

        self.btnMinimize = QPushButton('Minimize', self)
        self.btnMinimize.move(60*4, 0)
        self.btnMinimize.resize(60, 20)
        self.btnMinimize.clicked.connect(self.showMinimized)

        self.btnClose = QPushButton('Quit', self)
        self.btnClose.move(60*5, 0)
        self.btnClose.resize(60, 20)
        self.btnClose.clicked.connect(qApp.quit)

        self.output = QTextEdit(self)
        self.output.setLineWrapMode(0)
        self.output.move(0, 20)
        self.output.resize(600, 200)

        self.textFormat = QTextCharFormat()
        self.textFormat.setFont(QFont("Courier New"))
        #self.textFormat.setFont(QFont("Source Code Pro"))
        self.textFormat.setFontPointSize(10)

        self.process = QProcess(self)
        self.process.readyReadStandardOutput.connect(self.dataStandardReady)
        self.process.readyReadStandardError.connect(self.dataErrorReady)

        self.process.started.connect(self.processStart)
        self.process.finished.connect(self.processStop)

        self.setFixedSize(600, 220)
        self.setWindowTitle('BlobIDE')
        self.show()


    def processStart(self):
        self.output.clear()
        self.btnGenerate.setEnabled(False)
        self.btnBuild.setEnabled(False)
        self.btnRun.setEnabled(False)
        self.btnClean.setEnabled(False)
        self.btnMinimize.setEnabled(False)
        self.btnClose.setEnabled(False)

    def processStop(self):
        self.btnGenerate.setEnabled(True)
        self.btnBuild.setEnabled(True)
        self.btnRun.setEnabled(True)
        self.btnClean.setEnabled(True)
        self.btnMinimize.setEnabled(True)
        self.btnClose.setEnabled(True)

    def run(self):
        self.process.start("cmake", ["--build", "build"])

    def build(self):
        self.process.start("cmake", ["--build", "build"])

    def generate(self):
        self.process.start("cmake", ["-H.", "-Bbuild", "-G", "MSYS Makefiles", "-DCMAKE_BUILD_TYPE=Debug"])

    def clean(self):
        self.process.start("rm", ["-rf", "build"])

    def consoleWrite(self, data):
        cursor = self.output.textCursor()
        cursor.movePosition(cursor.End)
        data = str(data.data(), encoding='utf-8')
        splitANSI = re.compile(
            r"""(?P<code>([;\d]*[A-Za-z]))(?P<text>.*)"""
            , re.VERBOSE).match

        escapeStart = ''.join([chr(0x1B), chr(0x5B)])

        while escapeStart in data:
            subdata = data.partition(escapeStart)
            cursor.insertText(subdata[0], self.textFormat)
            
            split = splitANSI(subdata[2]).groupdict()
            if split['code'][-1:] == "m" and split['code'][:-1].isdigit():
                code = int(split['code'][:-1])
                
            data = split['text']
        
        cursor.insertText(data, self.textFormat)

        self.output.ensureCursorVisible()

    def dataErrorReady(self):
        self.consoleWrite(self.process.readAllStandardError())

    def dataStandardReady(self):
        self.consoleWrite(self.process.readAllStandardOutput())


if __name__ == '__main__':
    app = QApplication(sys.argv)
    mainWindow = MainWindow()
    sys.exit(app.exec_())
