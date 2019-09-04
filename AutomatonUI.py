# -*- coding: utf-8 -*-
"""
UI to display the robot moves for a 2D bounding box task
Dan Biediger
2019
University of Houston
"""
import tkinter as tk
from tkinter import ttk
import Board

class AutomatonUIApp:

    def __init__(self, master):
        self.board = Board.Board((7,8), (7,9))
        self.frameMain = tk.Frame(master, width=1920, height=1080, bd=1)
        self.frameMain.pack(side=tk.LEFT)
        self.canvasBoard = tk.Canvas(self.frameMain, width=1200, height=900)
        self.canvasBoard.pack(side=tk.LEFT, fill=tk.BOTH)
        self.frame = tk.Frame(master, bd=2, relief=tk.RAISED)
        self.frame.pack(side=tk.RIGHT, fill=tk.BOTH)
        
        #self.genButton = tk.Button(self.frame, text='Run', command=self.Run)        
        #self.genButton.pack(side=tk.TOP)
        self.labelTop = tk.Label(self.frame, text = "1. Select a Polyomino configuration")
        self.labelTop.pack(side=tk.TOP)
                
        self.tkvar = tk.StringVar(master)
        self.choices = {"single", "simpeleZ", "smallL", "spiral!"}
        self.tkvar.set("simpleZ")
        self.popupMenu = tk.OptionMenu(self.frame, self.tkvar, *self.choices)
        self.tkvar.trace('w', self.SetPolyomino)
        self.popupMenu.pack(side=tk.TOP)
        
        #self.showPath = tk.IntVar()
        #self.pathBox = tk.Checkbutton(self.frame, text='Path', command=self.DrawPath, variable=self.showPath)
        #self.pathBox.pack(side=tk.TOP)
        #self.pathButton = tk.Button(self.frame, text='Path', command=self.DrawPath)        
        #self.pathButton.pack(side=tk.TOP)        
        #self.iterateButton = tk.Button(self.frame, text='Iterate', command=self.Iterate)        
        #self.iterateButton.pack(side=tk.BOTTOM)   

        self.slider = tk.Scale(self.frame, from_=0, to=200, orient=tk.VERTICAL, 
                               resolution=1, length=400, sliderlength=20, command=self.SetCurrentStep)
        self.slider.pack(side=tk.BOTTOM)

        #self.fillButton = tk.Button(self.frame, text='Fill', command=self.DrawFill)        
        #self.fillButton.pack(side=tk.TOP)        
        
        #self.button = tk.Button(self.frame, text="QUIT", fg="red", command=self.frame.quit)
        #self.button.pack(side=tk.BOTTOM)
        
        self.DrawBoard()
    
    def DrawBoard(self):
        self.canvasBoard.delete(tk.ALL)
        self.board.Draw(self.canvasBoard,(800,800))
        self.canvasBoard.update()


    def Run(self):
        # Disabled for now
        #self.board.Update()
        self.DrawBoard()
        
    
    def SetCurrentStep(self, value):
        step = self.slider.get()
        self.board.SetStep(step)
        self.DrawBoard()
    
    
    def SetPolyomino(self, *args):
        print(self.tkvar.get())
        self.board.SetPolyomino(self.tkvar.get())
        self.DrawBoard()
    
    
root = tk.Tk()

app = AutomatonUIApp(root)

root.mainloop()
root.destroy()
