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
        self.canvasResult = tk.Canvas(self.frameMain, width=300, height=950)
        self.canvasResult.pack(side=tk.LEFT, fill=tk.BOTH)
        self.canvasBoard = tk.Canvas(self.frameMain, width=900, height=950)
        self.canvasBoard.pack(side=tk.LEFT, fill=tk.BOTH)
        self.controlFrame = tk.Frame(master, bd=2, relief=tk.RAISED)
        self.controlFrame.pack(side=tk.RIGHT, fill=tk.BOTH)
        self.tabControl = ttk.Notebook(self.controlFrame)
        
        self.tab1 = ttk.Frame(self.tabControl)
        self.tabControl.add(self.tab1, text='Control')
        self.tab2 = ttk.Frame(self.tabControl)
        self.tabControl.add(self.tab2, text='Settings')
        self.tabControl.pack(expand=1, fill="both")
        
        self.labelTop = tk.Label(self.tab1, text = "Select a Polyomino configuration")
        self.labelTop.pack(side=tk.TOP)
                
        self.tkvar = tk.StringVar(master)
        self.choices = self.board.GetChoices()
        self.tkvar.set(self.choices[0])
        self.popupMenu = tk.OptionMenu(self.tab1, self.tkvar, *self.choices)
        self.tkvar.trace('w', self.SetPolyomino)
        self.popupMenu.pack(side=tk.TOP)
        
        self.iterateButton = tk.Button(self.tab1, text='Iterate', command=self.Iterate)        
        self.iterateButton.pack(side=tk.BOTTOM)
        #self.iterateButton = tk.Button(self.controlFrame, text='Results!', command=self.GenerateResults)        
        #self.iterateButton.pack(side=tk.BOTTOM)

        self.slider = tk.Scale(self.tab1, from_=0, to=Board.MAX_MOVES, orient=tk.VERTICAL, 
                               resolution=1, length=800, sliderlength=20, command=self.SetCurrentStep)
        self.slider.pack(side=tk.BOTTOM)
        
        # Settings Tab
        self.axisButton = tk.Button(self.tab2, text='Hide Axes', command=self.ToggleShowAxes)        
        self.axisButton.pack(side=tk.TOP)
        
        self.SetPolyomino()
        
    
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
        self.slider.configure(to=self.board.GetMoveCount()-1) #Note the need to offset by 1 for one-off errors
        self.slider.update()
        self.DrawBoard()
        
        for name,value in zip(["Initial Search", "Add/Shift Tile", "Delete Tile", "Move/Search"], self.board.results[4]):
            print("{} - {}".format(name, value))
        
        print("Total Moves: {}".format(sum(self.board.results[4])))
        
    
    def Iterate(self):
        for step in range(self.board.GetMoveCount()):
            self.slider.set(step)
            self.canvasBoard.update()
            self.canvasResult.update()
            time.sleep(1/15)
            
    
    def ToggleShowAxes(self):
        if self.axisButton.config('text')[-1] == 'Show Axes':
            # Turn the Axis on
            self.axisButton.config(text='Hide Axes')
            self.board.showAxes = True
        else:
            # Turn the Axis off
            self.axisButton.config(text='Show Axes')
            self.board.showAxes = False

        self.DrawBoard() # Redraw the board
    
            
    def GenerateResults(self):
        choices = ["single", "L02", "L04", "L08", "L16", "L32", "U02", "U04", "U08",
                   "U16", "U32", "C02", "C04", "C08", "C16", "C32", "n02", "n04",
                   "n08", "n16", "n32", "SQ02", "SQ04", "SQ08", "SQ16", "SQ32",
                   u"\u229002", u"\u229004", u"\u229008", u"\u229016", u"\u229032"]
        
        print("Results:")
        print("="*20)
        for choice in choices:
            print(choice)
            self.board.SetPolyomino(choice)
            self.slider.set(0)
            self.slider.update()
            self.DrawBoard()
            print(self.board.results[4], sum(self.board.results[4]))
        print("="*20)    
    
    
root = tk.Tk()
root.title("2D Tile Simulation")

app = AutomatonUIApp(root)

root.mainloop()
#root.destroy()
