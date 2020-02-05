# -*- coding: utf-8 -*-
"""
UI to display the robot moves for a 2D bounding box task
Dan Biediger
2019
University of Houston
"""
import tkinter as tk
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
        self.choices = self.board.GetChoices()
        self.tkvar.set(self.choices[0])
        self.popupMenu = tk.OptionMenu(self.frame, self.tkvar, *self.choices)
        self.tkvar.trace('w', self.SetPolyomino)
        self.popupMenu.pack(side=tk.TOP)
        
        self.iterateButton = tk.Button(self.frame, text='Iterate', command=self.Iterate)        
        self.iterateButton.pack(side=tk.BOTTOM)
        #self.iterateButton = tk.Button(self.frame, text='Results!', command=self.GenerateResults)        
        #self.iterateButton.pack(side=tk.BOTTOM)

        self.slider = tk.Scale(self.frame, from_=0, to=Board.MAX_MOVES, orient=tk.VERTICAL, 
                               resolution=1, length=800, sliderlength=20, command=self.SetCurrentStep)
        self.slider.pack(side=tk.BOTTOM)
        
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
        for step in range(800):
            temp = self.board.SetStep(step)
            self.DrawBoard()
            time.sleep(0.1)
            if temp:
                return
            
            
    def GenerateResults(self):
        choices = ["single", "L2", "L4", "L8", "L16", "L32", "U2", "U4", "U8",
                   "U16", "U32", "C2", "C4", "C8", "C16", "C32", "n2", "n4",
                   "n8", "n16", "n32", "SQ2", "SQ4", "SQ8", "SQ16", "SQ32",
                   u"\uA73E2", u"\uA73E4", u"\uA73E8", u"\uA73E16", u"\uA73E32"]
        
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

app = AutomatonUIApp(root)

root.mainloop()
#root.destroy()
