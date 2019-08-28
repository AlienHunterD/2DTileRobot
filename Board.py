# -*- coding: utf-8 -*-
"""
Maze creation and solver demo

@author: d
"""
import numpy as np
import tkinter
import random
from time import clock
#from Robot import *

class Board:
    
    def __init__(self, start1, start2, dims=(10,10)):
        """ Create an empy maze of dimension given by dims """
        self.robot1 = tuple(start1+(1,))
        self.robot2 = tuple(start2+(-1,))
        self.size = dims        
        self.width, self.height = dims
        self.tiles = np.zeros(dims, dtype=int)
        self.Generate()

    
    def _DrawGrid(self, canvas, size, offset):
        deltaX = int(size[0]/self.width) #Change here for non square cells
        deltaY = int(size[1]/self.height) #Change here for non square cells
        for x in range(offset,self.width*deltaX+offset+1,deltaX): #Draw the simple outline
            canvas.create_line(x, offset, x, self.height*deltaY+offset, 
                               fill='#c0c0c0')#Vertical lines
            
        for y in range(offset,self.height*deltaY+offset+1,deltaY): #Draw the simple outline
            canvas.create_line(offset, y, self.width*deltaX+offset, y, 
                               fill='#c0c0c0')#Horizontal lines
        
        for x in range(self.width): # Draw the column numbers
            loc = (x*deltaX+3*deltaX/4, self.height*deltaY+offset+5)
            canvas.create_text(loc, anchor='nw', text="{}".format(x))
        for y in range(self.height): # Draw the row numbers
            loc = (10,(self.height-y-1)*deltaY+3*deltaY/4)
            canvas.create_text(loc, anchor='nw', text="{}".format(y))

                         
    def Draw(self, canvas, size = (600,600), offset = 20):
        self._DrawGrid(canvas, size, offset)
        deltaX = int(size[0]/self.width) #Change here for non square cells
        deltaY = int(size[1]/self.height) #Change here for non square cells
        
        for v in range(self.height):
            for u in range(self.width):
                if self.tiles[u,v] == 1:
                    x = offset + u*deltaX 
                    y = offset + (self.height-v-1)*deltaY #FLip the y
                    canvas.create_rectangle((x+1, y+1, x+deltaX-1, y+deltaY-1), 
                               fill="gray")

        # Draw both of the robots on the board
        u, v = self.robot1[:2]
        x = offset + u*deltaX 
        y = offset + (self.height-v-1)*deltaY # Flip the y
        canvas.create_oval((x+2, y+2, x+deltaX-2, y+deltaY-2),fill="red")
        canvas.create_text((x+deltaX/2, y+deltaY/2), anchor='center', text=str(self.robot1[2]))
        
        u, v = self.robot2[:2]
        x = offset + u*deltaX 
        y = offset + (self.height-v-1)*deltaY # Flip the y
        canvas.create_oval((x+2, y+2, x+deltaX-2, y+deltaY-2),fill="blue")
        canvas.create_text((x+deltaX/2, y+deltaY/2), anchor='center', text=str(self.robot2[2]))

        canvas.create_text((20,18), anchor='sw', text="{}x{}".format(self.width,self.height))
        
        
    def Generate(self):
        """ Generate the initial tile setup. """
        self.tiles.fill(0)
        self.tiles[(3,6)] = 1
        self.tiles[(4,6)] = 1
        self.tiles[(4,5)] = 1
        self.tiles[(5,5)] = 1

    
    def Update(self):
        #self.robot1.Update()
        loc =  (self.robot1[0],self.robot1[1])
        loc_south = (self.robot1[0],self.robot1[1]-1)
        loc_east = (self.robot1[0]+1,self.robot1[1])
        loc_west = (self.robot1[0]-1,self.robot1[1])
        
        if self.robot1[2] == 1: #this robot must search for bottom
            #look south
            print('moving south!')
            if self.tiles[loc_south] == 1: #is a tile
                #move robot down one, state is still searching down
                self.robot1 = loc_south + (1,)
                self.robot2 = (self.robot2[0],self.robot2[1]-1,self.robot2[2])
            elif  self.tiles[loc_south] == 0: 
                #move robot down one, state is not searching down
                self.robot1 = loc_south + (2,)
                self.robot2 = (self.robot2[0],self.robot2[1]-1,self.robot2[2])
        elif self.robot1[2] == 2: #this robot must search for bottom by going right or left 
            if self.tiles[loc_east] == 1: #is a tile
                #move right, go back to searching down
                self.robot1 = loc_east + (1,)
                self.robot2 = (self.robot2[0]+1,self.robot2[1],self.robot2[2])
            elif self.tiles[loc_west] == 1: #is a tile
                #move west, go back to searching down
                self.robot1 = loc_west + (1,)
                self.robot2 = (self.robot2[0]-1,self.robot2[1],self.robot2[2])
            elif self.tiles[loc_south] == 1: #is a tile
                self.robot1 = loc_south + (1,)
                self.robot2 = (self.robot2[0],self.robot2[1]-1,-2)
            else:
                self.robot1 = loc_south + (3,)
                self.robot2 = (self.robot2[0],self.robot2[1]-1,-2)
        elif self.robot1[2] == 3: #IS IT OK TO START BOUNDING BOX?
            if self.tiles[loc_east] == 1: #is a tile
                #move right, go back to searching down
                self.robot1 = loc_east + (1,)
                self.robot2 = (self.robot2[0]+1,self.robot2[1],self.robot2[2])
            elif self.tiles[loc_west] == 1: #is a tile
                #move west, go back to searching down
                self.robot1 = loc_west + (1,)
                self.robot2 = (self.robot2[0]-1,self.robot2[1],self.robot2[2])
            elif self.tiles[loc_south] == 1: #is a tile
                self.robot1 = loc_south + (1,)
                self.robot2 = (self.robot2[0],self.robot2[1]-1,-2)
            else:
                self.robot1 = loc + (4,)

        elif self.robot1[2] == 4: #Place a tile where robot1 is
                self.robot1 = loc_west + (4,)
                self.tiles[loc] = 1
                # if no tile is to the right
                
                    
                
    
    
    
    @staticmethod
    def _Hexify(num):
        temp = hex(num)[2:]
        if len(temp) < 2:
            temp = '0' + temp
        
        return temp

    
    @staticmethod
    def GetColor(ratio):
        if ratio < 0.0:
            return '#ffffff'
        if ratio == 0.0:
            return '#ff0000'
        if ratio >= 1.0:
            return '#ff00ff'
            
        temp = ratio * 5
        if temp < 1.0:
            temp = int(temp * 256)
            return '#ff'+Maze._Hexify(temp)+'00'
        elif temp < 2.0:
            temp = 255-int((temp - 1.0) * 256)
            return '#'+Maze._Hexify(temp)+'ff00'
        elif temp < 3.0:
            temp = int((temp - 2.0) * 256)
            return '#00ff'+Maze._Hexify(temp)
        elif temp < 4.0:
            temp = 255-int((temp - 3.0) * 256)
            return '#00'+Maze._Hexify(temp)+'ff'
        else:
            temp = int((temp - 4.0) * 256)
            return '#'+Maze._Hexify(temp)+'00ff'
            
