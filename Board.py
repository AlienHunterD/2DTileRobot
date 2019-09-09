# -*- coding: utf-8 -*-
"""
The Board and related logic for finding a bounding box around a connected 
2D polyomino as presented in the paper "Connected Assembly and Reconfiguration by Finite Automata" 
Dan Biediger
2019
University of Houston
"""
import numpy as np
import tkinter
import MoveLog
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
STATE_BUILDINGBB = 3
STATE_FORGEAHEAD = 4
STATE_SHIFT_BEGIN = 11
STATE_SHIFT_BLOCK = 12
STATE_SHIFT_CONTINUE = 13
STATE_SHIFT_UNDO = 20
STATE_FOLLOWBB_CW = 22
STATE_FOLLOWBB_CW_LOOK4MARKER = 23
STATE_FOLLOWBB_CW_COMPLETE = 24 
STATE_BACKTRACK = 6
STATE_CHECKFORWARD = 7
STATE_SHIFT = 8
STATE_FINISH = 10
STATE_TILE_MEMBERSHIP_SET_MARKER = 30
STATE_TILE_MEMBERSHIP_CHEAPCHECK = 31
STATE_TILE_MEMBERSHIP_START_SEARCH = 32
STATE_TILE_MEMBERSHIP_SEARCH = 33
STATE_SHIFT_AND_CLOSE = 44
STATE_CLOSE_THE_GAP = 49
STATE_FIND_ROBOT2_TO_DELETE = 50
STATE_FOLLOW_ME_AND_DELETE = 51
STATE_MOVE_PAST_ROBOT2 = 40
STATE_MARK_START = -1
STATE_MOVE_HOME = -2

class Board:
    def __init__(self, dims=(16,16)):
        """ Create a board of the dimension given """
        #TODO: dictionary for left, right, forward, backward tile locations
        # TODO: names for states
        self.robot1 = [[7,8], STATE_SEARCHSOUTH, SOUTH]   # Start at the location in state 1, facing South
        self.robot2 = [[7,9], STATE_IDLE, SOUTH] # Start at the location in state 0, facing South
        self.results = [0,0,0]
        self.size = dims        
        self.width, self.height = dims
        self.tiles = np.zeros(dims, dtype=int)
        self.log = MoveLog.MoveLog()
        self.SetPolyomino()
        self.SetStep(0) # Go back to the beginning
    
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
    
    def ShowResults(self, canvas, size = (400,400), offset = 20):
        steps,moves,placed,picked = self.results
        canvas.create_text((offset, 30), anchor='nw', font=("Purisa", 14), text="Step: {}".format(steps))
        canvas.create_text((offset, 60), anchor='nw', font=("Purisa", 14), text="Robot Moves: {}".format(moves))
        canvas.create_text((offset, 90), anchor='nw', font=("Purisa", 14), text="Tiles Placed: {}".format(placed))
        canvas.create_text((offset, 120), anchor='nw', font=("Purisa", 14), text="Tiles Removed: {}".format(picked))

        
    def Generate(self):
        """ Generate the initial tile setup. """
        
        for i in range(800): # Run out 100 steps in the sim
            self.Update()
        
        self.SetStep(0) # Go back to the beginning
        
    
    def Update(self):
        #self.robot1.Update()
        loc =  tuple(self.robot1[0])
        
        if self.CheckState(self.robot2, STATE_MARK_START):
            self.SetState(self.robot2, STATE_IDLE)
        elif self.CheckState(self.robot2, STATE_MOVE_HOME):            
            self.MoveRobotBackward(self.robot2)
            self.TurnRobotLeft(self.robot2)
            self.SetState(self.robot2, STATE_IDLE)
            #self.MoveRobotForward(self.robot2)
        
        #if self.LookForRobot():
        #    print("Found a robot!")
        #    self.log.LogState(self.tiles, self.robot1, self.robot2, "Finished!")
        #    return
        # ********************************************************************************
        # Start searching to the south for a place to start
        # ********************************************************************************
        if self.CheckState(self.robot1, STATE_SEARCHSOUTH): #this robot must search for bottom
            self.SearchSouth()
        # ********************************************************************************
        # After searching south look east and west for a path to continue south    
        # ********************************************************************************
        elif self.CheckState(self.robot1, STATE_SEARCH_EAST_WEST): #this robot must search for bottom by going right or left
            self.SearchEastWest()
        # ********************************************************************************            
        #
        # ********************************************************************************
        elif self.CheckState(self.robot1, STATE_BUILDINGBB): # We are building the Bounding box
            if self.LookRight(self.robot1) and self.LookLeft(self.robot1) and self.LookAhead(self.robot1):
                self.TurnRobotRight(self.robot1)
                self.MoveRobotForward(self.robot1)
                self.PlaceTile(loc) # Place a tile on the square that I left
                self.SetState(self.robot1,STATE_FORGEAHEAD)
            else:
                if not self.LookAhead(self.robot1):
                    self.SetState(self.robot1, STATE_TILE_MEMBERSHIP_CHEAPCHECK) #Start to figure out what we are doing
                    self.MoveRobotForward(self.robot1)
                elif self.LookLeft(self.robot1): # We see something, but not on the left and need to shift left
                    self.SetState(self.robot1, STATE_SHIFT_BEGIN)
                else:
                    self.SetState(self.robot1, STATE_BACKTRACK)
        # ********************************************************************************
        #
        # ********************************************************************************
        elif self.CheckState(self.robot1, STATE_SHIFT_BEGIN):
            #self.MoveRobotBackward(self.robot1)
            if not self.LookLeft(self.robot1):
                self.MoveRobotBackward(self.robot1)
                self.SetState(self.robot1, STATE_BACKTRACK)
            else:
                self.PlaceTile(loc)
                self.SetState(self.robot1, STATE_SHIFT_BLOCK)
        # ********************************************************************************
        #
        # ********************************************************************************
        elif self.CheckState(self.robot1, STATE_SHIFT_BLOCK):
            if self.LookBehind(self.robot1):
                self.TurnRobotLeft(self.robot1)
                self.SetState(self.robot1, STATE_FOLLOWBB_CW)
            else:
                self.MoveRobotBackward(self.robot1)
                self.RemoveTile(loc)
                self.TurnRobotLeft(self.robot1)
                self.MoveRobotForward(self.robot1)
                if self.LookAhead(self.robot1):
                    self.PlaceTile(tuple(self.robot1[0])) # Place the tile in the space where the robot now is
                    self.SetState(self.robot1, STATE_SHIFT_CONTINUE) 
                else:
                    self.MoveRobotBackward(self.robot1)
                    self.TurnRobotRight(self.robot1)
                    self.SetState(self.robot1, STATE_SHIFT_UNDO)
        # ********************************************************************************
        
        # ********************************************************************************
        elif self.CheckState(self.robot1, STATE_SHIFT_UNDO):
            self.MoveRobotForward(self.robot1)
            if self.LookLeft(self.robot1):
                self.SetState(self.robot1, STATE_BACKTRACK)
            else:
                self.PlaceTile(tuple(self.robot1[0])) # Place the tile in the space adjacent to the roobot then move onto it
                locLeft = self.GetLocation(self.robot1, COUNTERCLOCKWISE[self.robot1[2]])
                self.RemoveTile(locLeft)
        # ********************************************************************************
        
        # ********************************************************************************
        elif self.CheckState(self.robot1, STATE_SHIFT_CONTINUE):
            self.MoveRobotBackward(self.robot1)
            self.TurnRobotRight(self.robot1)
            self.SetState(self.robot1, STATE_SHIFT_BLOCK)
        # ********************************************************************************
        #
        # ********************************************************************************            
        elif self.CheckState(self.robot1, STATE_FORGEAHEAD): # Move forward after a turn to the right
            if self.LookRight(self.robot1) and self.LookLeft(self.robot1) and self.LookAhead(self.robot1):
                self.MoveRobotForward(self.robot1)
                self.PlaceTile(loc) # Place a tile on the square that I left
                self.SetState(self.robot1,STATE_BUILDINGBB)
            else:
                if not self.LookAhead(self.robot1):
                    self.SetState(self.robot1, STATE_TILE_MEMBERSHIP_CHEAPCHECK) #Start to figure out what we are doing
                    self.MoveRobotForward(self.robot1)
                else:
                    self.SetState(self.robot1, STATE_BACKTRACK)
        # ********************************************************************************
        #
        # ********************************************************************************
        elif self.CheckState(self.robot1, STATE_TILE_MEMBERSHIP_CHEAPCHECK): # Step on to the tile ahead and do the cheap check
            if self.LookForRobot():
                if self.IsRobot1BehindRobot2(): 
                    self.MoveRobotBackward(self.robot1) # On the Polyomino
                    self.SetState(self.robot1, STATE_SHIFT_BEGIN)
                else:
                    if self.IsRobot2AtRightOfRobot1():
                        locBack = self.GetLocation(self.robot1, BEHIND[self.robot1[2]])
                        self.PlaceTile(locBack) # Place a tile on the square that I left
                        self.SetState(self.robot1, STATE_FINISH)
                    # if Robot1 came from below, there is 
                    else:
                        pass # We need to do some shifting to fix this
            elif self.CountNeighbors(self.robot1) == 3 or self.CountNeighbors(self.robot1) == 1: # this is p
                self.MoveRobotBackward(self.robot1)
                self.SetState(self.robot1, STATE_SHIFT_BEGIN)
                # This is a polyonmino
            else: # Explore to determine if this is p or bb
                self.MoveRobotBackward(self.robot1)
                self.SetState(self.robot1, STATE_TILE_MEMBERSHIP_SET_MARKER)
                # To DO: Set the marker here and explore the polyomino
        # ********************************************************************************
        #
        # ********************************************************************************            
        elif self.CheckState(self.robot1, STATE_TILE_MEMBERSHIP_SET_MARKER):
            self.MoveRobotBackward(self.robot1)
            if self.LookBehind(self.robot1):
                locBack = self.GetLocation(self.robot1, BEHIND[self.robot1[2]])
                self.PlaceTile(locBack) # Place a tile on the square that I left
            self.SetState(self.robot1, STATE_TILE_MEMBERSHIP_START_SEARCH)
            
        # ********************************************************************************
        #
        # ********************************************************************************            
        elif self.CheckState(self.robot1, STATE_TILE_MEMBERSHIP_START_SEARCH):
            self.MoveRobotForward(self.robot1)
            self.SetState(self.robot1, STATE_TILE_MEMBERSHIP_SEARCH)
        # ********************************************************************************
        #
        # ********************************************************************************            
        elif self.CheckState(self.robot1, STATE_TILE_MEMBERSHIP_SEARCH):
            self.MoveRobotForward(self.robot1)
            if self.LookForRobot():
                if self.IsRobot1BehindRobot2(): # we are in p
                    self.robot1[2] = self.robot2[2] # Orient robot 1 to match robot 2
                    self.TurnRobotRight(self.robot2)
                    self.MoveRobotForward(self.robot2)
                    self.SetState(self.robot1, STATE_MOVE_PAST_ROBOT2)
                else: # I am not in p
                    self.TurnRobotRight(self.robot1)
                    self.TurnRobotRight(self.robot1)
                    self.SetState(self.robot1, STATE_FOLLOWBB_CW_COMPLETE)
                    # We are below the robot
            elif not self.LookRight(self.robot1):
                self.TurnRobotRight(self.robot1)
            elif not self.LookAhead(self.robot1):
                pass
            elif not self.LookLeft(self.robot1):
                self.TurnRobotLeft(self.robot1)
            else:
                self.TurnRobotRight(self.robot1)
                self.TurnRobotRight(self.robot1)

        # ********************************************************************************
        #
        # ********************************************************************************            
        elif self.CheckState(self.robot1, STATE_MOVE_PAST_ROBOT2):
            self.MoveRobotForward(self.robot1)
            self.SetState(self.robot1, STATE_FOLLOWBB_CW_LOOK4MARKER)
            self.SetState(self.robot2, STATE_MOVE_HOME)


        # ********************************************************************************
        #
        # ********************************************************************************            
        elif self.CheckState(self.robot1, STATE_BACKTRACK):
            # look behind
            if self.LookBehind(self.robot1): # See if there is a tile behind me
                self.TurnRobotLeft(self.robot1)
                self.SetState(self.robot1, STATE_CHECKFORWARD)
            else:
                self.RemoveTile(loc)
                self.MoveRobotBackward(self.robot1)
        # ********************************************************************************
        #
        # ********************************************************************************                
        elif self.CheckState(self.robot1, STATE_CHECKFORWARD):
            if self.LookAhead(self.robot1): # if the square ahead is open
                self.MoveRobotForward(self.robot1)
                self.SetState(self.robot1, STATE_BUILDINGBB)
            else:
                self.SetState(self.robot1, STATE_BACKTRACK)
                
                
        # ********************************************************************************
        #
        # ********************************************************************************                
        elif self.CheckState(self.robot1, STATE_FOLLOWBB_CW_LOOK4MARKER):
            if not self.LookAhead(self.robot1):
                self.MoveRobotForward(self.robot1)
            elif not self.LookRight(self.robot1):
                self.TurnRobotRight(self.robot1)
                self.MoveRobotForward(self.robot1)
            elif not self.LookLeft(self.robot1):
                locLeft = self.GetLocation(self.robot1, COUNTERCLOCKWISE[self.robot1[2]])
                self.RemoveTile(locLeft)
                #locAhead = self.GetLocation(self.robot1, self.robot1[2])
                #self.PlaceTile(locAhead) # Place a tile on the square that I left
                self.SetState(self.robot1, STATE_CHECKFORWARD)
            else:
                self.MoveRobotForward(self.robot1)
                self.PlaceTile(tuple(self.robot1[0])) # Place the tile in the space where the robot now is
                self.SetState(self.robot1, STATE_SHIFT_BEGIN)
                
        
        # ********************************************************************************
        #
        # ********************************************************************************                
        elif self.CheckState(self.robot1, STATE_FOLLOWBB_CW_COMPLETE):
            if not self.LookAhead(self.robot1):
                self.MoveRobotForward(self.robot1)
            elif not self.LookRight(self.robot1):
                self.TurnRobotRight(self.robot1)
                self.MoveRobotForward(self.robot1)
            else:
                self.MoveRobotForward(self.robot1)
                # To Do: Chec here to see if a shif is needed to the left
                print("Stepped into the gap")
                lookAhead = list(map(add, self.robot1[0], MOVES[self.robot1[2]]))
                if self.CheckCorrnerTile(lookAhead): # We are at a corner, proceed
                    self.PlaceTile(tuple(self.robot1[0])) # Place the tile in the space where the robot now is
                    self.SetState(self.robot1, STATE_CLOSE_THE_GAP)
                else: # We are not on a coner, shift to find one
                    self.PlaceTile(tuple(self.robot1[0])) # Place the tile in the space where the robot now is
                    self.SetState(self.robot1, STATE_SHIFT_AND_CLOSE)
        
        # ********************************************************************************
        #
        # ********************************************************************************         
        elif self.CheckState(self.robot1, STATE_SHIFT_AND_CLOSE):
            if self.LookBehind(self.robot1):
                self.TurnRobotLeft(self.robot1)
                self.SetState(self.robot1, STATE_FOLLOWBB_CW_COMPLETE)
                print("Look for a corner again!")
            else:
                self.MoveRobotBackward(self.robot1)
                self.RemoveTile(loc)
                self.TurnRobotLeft(self.robot1)
                lookAhead = tuple(map(add, self.robot1[0], MOVES[self.robot1[2]]))
                self.PlaceTile(lookAhead) # Place
                self.TurnRobotRight(self.robot1)
                print("Keep Shifting")
        # ********************************************************************************
        #
        # ********************************************************************************                
        elif self.CheckState(self.robot1, STATE_CLOSE_THE_GAP):
            self.MoveRobotForward(self.robot1)
            self.TurnRobotRight(self.robot1)
            self.SetState(self.robot1, STATE_FIND_ROBOT2_TO_DELETE)
        
        # ********************************************************************************
        #
        # ********************************************************************************                
        elif self.CheckState(self.robot1, STATE_FIND_ROBOT2_TO_DELETE):
            self.MoveRobotForward(self.robot1)
            if self.LookForRobot():
                self.TurnRobotRight(self.robot1)
                self.TurnRobotRight(self.robot1)
                self.robot2[2] = self.robot1[2] # Share the orientation
                self.SetState(self.robot1, STATE_FOLLOW_ME_AND_DELETE)
        
        # ********************************************************************************
        #
        # ********************************************************************************                
        elif self.CheckState(self.robot1, STATE_FOLLOW_ME_AND_DELETE):
            self.MoveRobotForward(self.robot1)
            self.MoveRobotForward(self.robot2)
            self.RemoveTile(loc)
            if self.LookAhead(self.robot1): # I reached the end
                self.SetState(self.robot1, STATE_FINISH)
            # To Do: Fix this up
        
        # ********************************************************************************
        #
        # ********************************************************************************                
        elif self.CheckState(self.robot1, STATE_FOLLOWBB_CW):
            if not self.LookAhead(self.robot1):
                self.MoveRobotForward(self.robot1)
            elif not self.LookRight(self.robot1):
                self.TurnRobotRight(self.robot1)
                self.MoveRobotForward(self.robot1)
            else:
                self.SetState(self.robot1, STATE_CHECKFORWARD)
        self.log.LogState(self.tiles, self.robot1, self.robot2, " ", self.results)
        

    def SetPolyomino(self, poly="Default"):
        self.tiles.fill(0)
        start1 = [7,8]
        start2 = [7,9]
        
        if poly == "single":
            self.tiles[7,7] = 1
        elif poly == "spiral!":
            self.tiles[(7,8)] = 1
            self.tiles[(7,9)] = 1
            self.tiles[(7,10)] = 1
            self.tiles[(6,10)] = 1
            self.tiles[(5,10)] = 1
            self.tiles[(5,9)] = 1
            self.tiles[(5,8)] = 1
            self.tiles[(5,7)] = 1
            self.tiles[(5,6)] = 1     
            self.tiles[(5,5)] = 1
            self.tiles[(6,5)] = 1
            self.tiles[(7,5)] = 1
            self.tiles[(8,5)] = 1
            self.tiles[(9,5)] = 1
            self.tiles[(9,6)] = 1
            self.tiles[(9,7)] = 1
            self.tiles[(9,8)] = 1
            self.tiles[(9,9)] = 1
        elif poly == "smallL":
            self.tiles[(7,10)] = 1
            self.tiles[(7,9)] = 1
            self.tiles[(7,8)] = 1
            self.tiles[(7,7)] = 1
            self.tiles[(7,6)] = 1
            self.tiles[(8,6)] = 1
            self.tiles[(9,6)] = 1
            self.tiles[(10,6)] = 1
            self.tiles[(11,6)] = 1
        elif poly == "smallHook":
            self.tiles[(7,10)] = 1
            self.tiles[(7,9)] = 1
            self.tiles[(7,8)] = 1
            self.tiles[(7,7)] = 1
            self.tiles[(7,6)] = 1
            self.tiles[(8,6)] = 1
            self.tiles[(9,6)] = 1
            self.tiles[(10,6)] = 1
            self.tiles[(11,6)] = 1
            self.tiles[(11,11)] = 1
            self.tiles[(12,11)] = 1
            self.tiles[(12,10)] = 1
            self.tiles[(12,9)] = 1
            self.tiles[(12,8)] = 1
            self.tiles[(12,7)] = 1
            self.tiles[(12,6)] = 1
        elif poly == "UH":
            self.tiles[(3,12)] = 1
            self.tiles[(3,11)] = 1
            self.tiles[(3,10)] = 1
            self.tiles[(3,9)] = 1
            self.tiles[(3,8)] = 1
            self.tiles[(3,7)] = 1
            self.tiles[(4,7)] = 1
            self.tiles[(5,7)] = 1
            self.tiles[(6,7)] = 1
            self.tiles[(7,7)] = 1
            self.tiles[(7,8)] = 1
            self.tiles[(7,9)] = 1
            self.tiles[(7,10)] = 1
            self.tiles[(7,11)] = 1
            self.tiles[(7,12)] = 1
            # H
            self.tiles[(5,9)] = 1
            self.tiles[(5,8)] = 1
            self.tiles[(5,6)] = 1
            self.tiles[(5,5)] = 1
            self.tiles[(5,4)] = 1
            self.tiles[(5,3)] = 1
            self.tiles[(5,2)] = 1
            self.tiles[(6,5)] = 1
            self.tiles[(7,5)] = 1
            self.tiles[(8,5)] = 1
            self.tiles[(9,5)] = 1
            self.tiles[(9,6)] = 1
            self.tiles[(9,7)] = 1
            self.tiles[(9,8)] = 1
            self.tiles[(9,9)] = 1
            self.tiles[(9,4)] = 1
            self.tiles[(9,3)] = 1
            self.tiles[(9,2)] = 1
        elif poly == "backwardsC":
            self.tiles[(7,9)] = 1
            self.tiles[(7,8)] = 1
            self.tiles[(8,9)] = 1
            self.tiles[(9,9)] = 1
            self.tiles[(9,8)] = 1
            self.tiles[(9,7)] = 1
            self.tiles[(9,6)] = 1
            self.tiles[(9,5)] = 1
            self.tiles[(9,4)] = 1
            self.tiles[(8,4)] = 1
            self.tiles[(7,4)] = 1
        elif poly == "hookedN":
            self.tiles[(7,9)] = 1
            self.tiles[(7,8)] = 1
            self.tiles[(8,9)] = 1
            self.tiles[(9,9)] = 1
            self.tiles[(10,9)] = 1
            self.tiles[(10,8)] = 1
            self.tiles[(10,7)] = 1
            self.tiles[(10,6)] = 1
            self.tiles[(10,5)] = 1
            self.tiles[(10,4)] = 1
            self.tiles[(9,4)] = 1
            self.tiles[(8,4)] = 1
        else:
            self.tiles[(6,7)] = 1
            self.tiles[(7,7)] = 1
            self.tiles[(7,6)] = 1
            self.tiles[(8,6)] = 1
            
        self.log.Reset()
        self.robot1 = [start1, STATE_SEARCHSOUTH, SOUTH]   # Start at the location in state 1, facing South
        self.robot2 = [start2, STATE_IDLE, SOUTH] # Start at the location in state 0, facing South
        self.results = [0,0,0,0]
        self.log.LogState(self.tiles, self.robot1, self.robot2, "Initial Board State", self.results)
        self.Generate()

    def SetStep(self, step):
        self.tiles.fill(0)
        tile_list, self.robot1, self.robot2, message, self.results = self.log.GetStep(step)
        self.results[0] = step
        for loc in tile_list:
            self.tiles[loc] = 1
        
        return self.robot1[1] == STATE_FINISH

            
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
            
            
    def CheckCorrnerTile(self, loc):
        tile_hits = []
        for direction in MOVES:
            temp = tuple(map(add, loc, MOVES[direction]))
            if self.tiles[temp] == 1:
                tile_hits.append(direction)
        
        if len(tile_hits) != 2: # Corners must have 2 neighbors!
            return False
        
        return not((NORTH in tile_hits and SOUTH in tile_hits) or (EAST in tile_hits and WEST in tile_hits))
        
  
    def PlaceTile(self, loc):
        """ Place a tile at the tuple location. """
        self.tiles[loc] = 1
        self.results[2] +=1
    
    
    def RemoveTile(self, loc):
        """ Remove a tile from the tuple location. """ # ToDo: Add in a check to see if there is a tile there?
        self.tiles[loc] = 0
        self.results[3] +=1
    
    
    def MoveRobot(self, robot, direction):
        print("Look! {}".format(robot))
        robot[0] = list(map(add, robot[0], MOVES[direction]))
        self.results[1] += 1
    
    
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
        distance = abs(self.robot1[0][0] - self.robot2[0][0]) + abs(self.robot1[0][1] - self.robot2[0][1])
        return distance == 1
    
    
    def IsRobot1BehindRobot2(self):
        loc = self.GetLocation(self.robot2, BEHIND[self.robot2[2]])
        return loc == tuple(self.robot1[0])
    
    def IsRobot2AtRightOfRobot1(self):
        loc = self.GetLocation(self.robot1, CLOCKWISE[self.robot1[2]])
        return loc == tuple(self.robot2[0])
    
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
    
    def CountNeighbors(self, robot):
        count = 0
        for direction in MOVES:
            loc = self.GetLocation(robot, direction)
            if self.tiles[loc] == 1:
                count += 1
        return count
    
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
            
