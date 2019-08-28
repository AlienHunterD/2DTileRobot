# -*- coding: utf-8 -*-
"""
Maze creation and solver demo

@author: d
"""
import numpy as np
import tkinter
import random
from operator import add

NORTH = 1
EAST = 2
SOUTH = 4
WEST = 8
MOVES = {NORTH:[0,1], EAST:[1,0], SOUTH:[0,-1], WEST:[-1,0]} # Deltas for moves
BEHIND = {NORTH:SOUTH, EAST:WEST, SOUTH:NORTH, WEST:EAST}
CLOCKWISE = {NORTH:EAST, EAST:SOUTH, SOUTH:WEST, WEST:NORTH} #Turn Right
COUNTERCLOCKWISE = {NORTH:WEST, EAST:NORTH, SOUTH:EAST, WEST:SOUTH} #Turn Left

STATE_IDLE = 0
STATE_SEARCHSOUTH = 1
STATE_SEARCH_EAST_WEST = 2
STATE_BUILDINGBB = 4
STATE_BACKTRACK = 5
STATE_CHECKFORWARD = 6
STATE_FINISH = 7
STATE_MARK_START = -1

class Board:
    def __init__(self, start1, start2, dims=(15,15)):
        """ Create an empy maze of dimension given by dims """
        #TODO: dictionary for left, right, forward, backward tile locations
        # TODO: names for states
        self.robot1 = [list(start1), STATE_SEARCHSOUTH, SOUTH]   # Start at the location in state 1, facing South
        self.robot2 = [list(start2), STATE_IDLE, SOUTH] # Start at the location in state 0, facing South
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

    def DrawDirection(self, canvas, x,y,dx,dy,direction):
        points = [x + dx/2, y + 3, x + dx/4 + 1, y + dy/4 + 3, x + 3*dx/4 - 1, y + dy/4 + 3]
        
        if direction == SOUTH:
            points = [x + dx/2, y + dy - 3,  x + dx/4 + 1, y + 3*dy/4 - 3, x + 3*dx/4 - 1, y + 3*dy/4 - 3]
        elif direction == EAST:
            points = [x + 3*dx/4 - 1, y+dy/4+3, x + 3*dx/4 - 1, y + 3*dy/4-3, x+dx-3, y + dy/2]
        elif direction == WEST:
            points = [x + dx/4 - 1, y+dy/4+3, x + dx/4 - 1, y + 3*dy/4-3, x+3, y + dy/2]
        
        canvas.create_polygon(points, outline='black', fill='white', width=1)

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
        u, v = self.robot1[0]
        x = offset + u*deltaX 
        y = offset + (self.height-v-1)*deltaY # Flip the y
        canvas.create_oval((x+2, y+2, x+deltaX-2, y+deltaY-2),fill="red")
        self.DrawDirection(canvas, x, y, deltaX, deltaY, self.robot1[2])
        canvas.create_text((x+deltaX/2, y+deltaY/2), anchor='center', font=("Purisa", 14), text=str(self.robot1[1]))
        
        u, v = self.robot2[0]
        x = offset + u*deltaX 
        y = offset + (self.height-v-1)*deltaY # Flip the y
        canvas.create_oval((x+2, y+2, x+deltaX-2, y+deltaY-2),fill="blue")
        self.DrawDirection(canvas, x, y, deltaX, deltaY, self.robot2[2])
        canvas.create_text((x+deltaX/2, y+deltaY/2), anchor='center', font=("Purisa", 14), text=str(self.robot2[1]))

        canvas.create_text((20,18), anchor='sw', text="{}x{}".format(self.width,self.height))
        
        
    def Generate(self):
        """ Generate the initial tile setup. """
        self.tiles.fill(0)
        self.tiles[(6,7)] = 1
        self.tiles[(7,7)] = 1
        self.tiles[(7,6)] = 1
        self.tiles[(8,6)] = 1
        

    
    def Update(self):
        #self.robot1.Update()
        loc =  tuple(self.robot1[0])
        
        if self.CheckState(self.robot2, STATE_MARK_START):
            self.SetState(self.robot2, STATE_IDLE)
            self.MoveRobotForward(self.robot2)
        
        if self.LookForRobot():
            print("Found a robot!")
            return
        
        if self.CheckState(self.robot1, STATE_SEARCHSOUTH): #this robot must search for bottom
            self.SearchSouth()
            
        elif self.CheckState(self.robot1, STATE_SEARCH_EAST_WEST): #this robot must search for bottom by going right or left
            self.SearchEastWest()
 
        elif self.CheckState(self.robot1, STATE_BUILDINGBB):
            
            if self.LookRight(self.robot1) and self.LookLeft(self.robot1) and self.LookAhead(self.robot1):
                self.TurnRobotRight(self.robot1)
                self.MoveRobotForward(self.robot1)
                self.PlaceTile(loc) # Place a tile on the square that I left
            else:
                self.SetState(self.robot1, STATE_BACKTRACK)
        elif self.CheckState(self.robot1, STATE_BACKTRACK):
            # look behind
            if self.LookBehind(self.robot1): # See if there is a tile behind me
                self.TurnRobotLeft(self.robot1)
                self.SetState(self.robot1, STATE_CHECKFORWARD)
            else:
                self.RemoveTile(loc)
                self.MoveRobotBackward(self.robot1)
        elif self.CheckState(self.robot1, STATE_CHECKFORWARD):
            if self.LookAhead(self.robot1): # if the square ahead is open
                self.MoveRobotForward(self.robot1)
                self.SetState(self.robot1, STATE_BUILDINGBB)
            else:
                self.SetState(self.robot1, STATE_BACKTRACK)
        
        print("{} -- {}".format(self.robot1, self.robot2))

            
    def SetState(self, robot, state):
        """ Set the state of the specified robot """
        robot[1] = state
    
    def CheckState(self, robot, state):
        return robot[1] == state

             
    def SearchSouth(self):
        """look south for another tile in P"""
        loc_south = self.GetLocation(self.robot1, SOUTH)
        
        if self.tiles[loc_south] == STATE_SEARCHSOUTH: #is a tile
            #move robot down one, state is still searching down
            self.MoveRobot(self.robot1, SOUTH)
            self.MoveRobot(self.robot2, SOUTH)
        elif self.tiles[loc_south] == 0: 
            #move robot down one, state is not searching down
            self.MoveRobot(self.robot1, SOUTH)
            self.MoveRobot(self.robot2, SOUTH)
            self.SetState(self.robot1, STATE_SEARCH_EAST_WEST) # Change the state to looking left and right
                

    def SearchEastWest(self):
        """look east and west for another tile in P"""
        loc_south = self.GetLocation(self.robot1, SOUTH)
        loc_east = self.GetLocation(self.robot1, EAST)
        loc_west = self.GetLocation(self.robot1, WEST)
        
        if self.tiles[loc_east] == 1: #is a tile
            #move right, go back to searching down
            self.MoveRobot(self.robot1, EAST)
            self.MoveRobot(self.robot2, EAST)
            self.SetState(self.robot1, STATE_SEARCHSOUTH) # Set robot1 to search for more tiles south
        elif self.tiles[loc_west] == 1: #is a tile
            #move west, go back to searching down
            self.MoveRobot(self.robot1, WEST)
            self.MoveRobot(self.robot2, WEST)
            self.SetState(self.robot1, STATE_SEARCHSOUTH) # Set robot1 to search for more tiles south
        elif self.tiles[loc_south] == 1: #is a tile
            self.MoveRobot(self.robot1, SOUTH)
            self.MoveRobot(self.robot2, SOUTH)
            self.SetState(self.robot1, STATE_SEARCHSOUTH) # Set robot1 to search for more tiles south
        else:
            self.MoveRobot(self.robot1, SOUTH)
            self.MoveRobot(self.robot2, SOUTH)
            self.SetState(self.robot1, STATE_BUILDINGBB) # Set robot1 to search for more tiles south
            self.SetState(self.robot2, STATE_MARK_START) # Get the second robot ready to move down
            
  
    def PlaceTile(self, loc):
        """ Place a tile at the tuple location. """
        self.tiles[loc] = 1
    
    def RemoveTile(self, loc):
        """ Remove a tile from the tuple location. """ # ToDo: Add in a check to see if there is a tile there?
        self.tiles[loc] = 0
    
    def MoveRobot(self, robot, direction):
        robot[0] = list(map(add, robot[0], MOVES[direction]))
    
    def GetLocation(self, robot, direction):
        return tuple(map(add, robot[0], MOVES[direction]))
    
    def MoveRobotForward(self, robot):
        self.MoveRobot(robot, robot[2])
    
    def MoveRobotBackward(self, robot):
        self.MoveRobot(robot, BEHIND[robot[2]])
    
    def TurnRobotRight(self, robot):
        robot[2] = CLOCKWISE[robot[2]]
    
    def TurnRobotLeft(self, robot):
        robot[2] = COUNTERCLOCKWISE[robot[2]]
    
    def LookForRobot(self):
        loc = self.GetLocation(self.robot1, self.robot1[2])
        print("{}({}-{}) - {}".format(loc, self.robot1[0], self.robot1[2], self.robot2[0]))
        if tuple(self.robot2[0]) == loc:
            self.SetState(self.robot1, STATE_FINISH)
            self.PlaceTile(tuple(self.robot1[0]))
            print("We Did it!!!")
            return True
        return False
    
    def LookAhead(self, robot):
        """ Returns true if the space ahead is open """
        loc = self.GetLocation(robot, robot[2])
        return self.tiles[loc] == 0
    
    def LookBehind(self, robot):
        """ Returns true if the space behind the robot is open """
        loc = self.GetLocation(robot, BEHIND[robot[2]])
        return self.tiles[loc] == 0 and tuple(self.robot2[0]) != loc
    
    def LookLeft(self, robot):
        """ Returns true if the space to the left of the robot is open """
        loc = self.GetLocation(robot, COUNTERCLOCKWISE[robot[2]])
        return self.tiles[loc] == 0 and tuple(self.robot2[0]) != loc
    
    def LookRight(self, robot):
        """ Returns true if the space to the right of the robot is open """
        loc = self.GetLocation(robot, CLOCKWISE[robot[2]])
        return self.tiles[loc] == 0 and tuple(self.robot2[0]) != loc
    
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
            
