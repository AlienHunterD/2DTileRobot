# -*- coding: utf-8 -*-
"""
UI to display the robot moves for a 2D bounding box task
Dan Biediger
2019
University of Houston
"""
import tkinter as tk
from tkinter import ttk
import time
import Board

class AutomatonUIApp:

    def __init__(self, master):
        self.board = Board.Board()
        self.frameMain = tk.Frame(master, width=1920, height=1080, bd=1)
        self.frameMain.pack(side=tk.LEFT)
        self.canvasResult = tk.Canvas(self.frameMain, width=450, height=900)
        self.canvasResult.pack(side=tk.LEFT, fill=tk.BOTH)
        self.canvasBoard = tk.Canvas(self.frameMain, width=900, height=900)
        self.canvasBoard.pack(side=tk.LEFT, fill=tk.BOTH)
        self.frame = tk.Frame(master, bd=2, relief=tk.RAISED)
        self.frame.pack(side=tk.RIGHT, fill=tk.BOTH)
        
        self.labelTop = tk.Label(self.frame, text = "1. Select a Polyomino configuration")
        self.labelTop.pack(side=tk.TOP)
                
        self.tkvar = tk.StringVar(master)
        self.choices = {"single", "simpeleZ", "L1", "L2", "L3", "L4", "L5", "L6", "L7",
                        "L8", "L9", "L10", "spiral!", "smallHook", "backwardsC", "hookedN", "UH"}
        self.tkvar.set("simpleZ")
        self.popupMenu = tk.OptionMenu(self.frame, self.tkvar, *self.choices)
        self.tkvar.trace('w', self.SetPolyomino)
        self.popupMenu.pack(side=tk.TOP)
        
        self.iterateButton = tk.Button(self.frame, text='Iterate', command=self.Iterate)        
        self.iterateButton.pack(side=tk.BOTTOM)   

        self.slider = tk.Scale(self.frame, from_=0, to=Board.MAX_MOVES, orient=tk.VERTICAL, 
                               resolution=1, length=800, sliderlength=20, command=self.SetCurrentStep)
        self.slider.pack(side=tk.BOTTOM)
        
        self.DrawBoard()
        
    
    def DrawBoard(self):
        self.canvasBoard.delete(tk.ALL)
        self.canvasResult.delete(tk.ALL)
        self.board.Draw(self.canvasBoard,(800,800))
        self.board.ShowResults(self.canvasResult,(400,800))
        self.canvasBoard.update()
        self.canvasResult.update()


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
        self.slider.set(0)
        self.slider.update()
        self.DrawBoard()
        print(self.board.results[4], sum(self.board.results[4]))
        
    
    def Iterate(self):
        for step in range(800):
            temp = self.board.SetStep(step)
            self.DrawBoard()
            time.sleep(0.1)
            if temp:
                return
    
    
root = tk.Tk()

app = AutomatonUIApp(root)

root.mainloop()
root.destroy()
