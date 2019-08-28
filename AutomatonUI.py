# -*- coding: utf-8 -*-
"""
Maze display UI

@author: d
"""
import tkinter as tk
from Board import *

class MazeUIApp:

    def __init__(self, master):
        self.board = Board((4,7), (4,8))
        self.frameMain = tk.Frame(master, width=1024, height=768, bd=1)
        self.frameMain.pack(side=tk.LEFT)
        self.canvasBoard = tk.Canvas(self.frameMain, width=900, height=700)
        self.canvasBoard.pack(side=tk.LEFT, fill=tk.BOTH)
        self.frame = tk.Frame(master, bd=2, relief=tk.RAISED)
        self.frame.pack(side=tk.RIGHT, fill=tk.BOTH)
        
        self.genButton = tk.Button(self.frame, text='Run', command=self.Run)        
        self.genButton.pack(side=tk.TOP)
        
        #self.showPath = tk.IntVar()
        #self.pathBox = tk.Checkbutton(self.frame, text='Path', command=self.DrawPath, variable=self.showPath)
        #self.pathBox.pack(side=tk.TOP)
        #self.pathButton = tk.Button(self.frame, text='Path', command=self.DrawPath)        
        #self.pathButton.pack(side=tk.TOP)        
        #self.iterateButton = tk.Button(self.frame, text='Iterate', command=self.Iterate)        
        #self.iterateButton.pack(side=tk.BOTTOM)   

        #self.slider = tk.Scale(self.frame, from_=25, to=75, orient=tk.HORIZONTAL)
        #self.slider.pack(side=tk.BOTTOM)

        #self.fillButton = tk.Button(self.frame, text='Fill', command=self.DrawFill)        
        #self.fillButton.pack(side=tk.TOP)        
        
        #self.button = tk.Button(self.frame, text="QUIT", fg="red", command=self.frame.quit)
        #self.button.pack(side=tk.BOTTOM)
        
        self.DrawBoard()
    
    def DrawBoard(self):
        self.canvasBoard.delete(tk.ALL)
        self.board.Draw(self.canvasBoard,(600,600))
        self.canvasBoard.update()


    def Run(self):
        print("running the 'Run' command")
        # Move the robots into starting position
        self.board.Update()
        self.DrawBoard()
        
               
root = tk.Tk()

app = MazeUIApp(root)

root.mainloop()
root.destroy()
