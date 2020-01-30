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
from enum import Enum,auto
import math

MAX_MOVES = 30000
NORTH = 1
EAST = 2
SOUTH = 4
WEST = 8
MOVES = {NORTH:[0,1], EAST:[1,0], SOUTH:[0,-1], WEST:[-1,0]} # Deltas for moves
BEHIND = {NORTH:SOUTH, EAST:WEST, SOUTH:NORTH, WEST:EAST}
CLOCKWISE = {NORTH:EAST, EAST:SOUTH, SOUTH:WEST, WEST:NORTH} #Turn Right
COUNTERCLOCKWISE = {NORTH:WEST, EAST:NORTH, SOUTH:EAST, WEST:SOUTH} #Turn Left

class STATE(Enum):
    IDLE = auto()
    SEARCHSOUTH = auto()
    SEARCH_EAST_WEST = auto()
    BUILDINGBB = auto()
    FORGEAHEAD_2 = auto()
    FORGEAHEAD_1 = auto()
    FORGEAHEAD_0 = auto()
    SHIFT_BEGIN = auto()
    SHIFT_PICK_BLOCK = auto()
    SHIFT_VALIDATE_PLACEMENT = auto()
    SHIFT_CONTINUE = auto()
    SHIFT_UNDO = auto()
    SHIFT_AHEAD = auto()
    PEPARE_2_SHIFT_LEFT = auto()
    FOLLOWBB_CW = auto()
    FOLLOWBB_CW_LOOK4MARKER = auto()
    FOLLOWBB_CW_COMPLETE = auto()
    BACKTRACK = auto()
    BRIDGE = auto()
    CHECKFORWARD = auto()
    SHIFT = auto()
    FINISH = auto()
    RETURN_2_BB = auto()
    TILE_MEMBERSHIP_MARKER_DECISION = auto()
    TILE_MEMBERSHIP_VALIDATE_MARKER = auto()
    TILE_MEMBERSHIP_CHEAPCHECK = auto()
    TILE_MEMBERSHIP_START_SEARCH = auto()
    TILE_MEMBERSHIP_SEARCH = auto()
    SHIFT_AND_CLOSE = auto()
    CLOSE_THE_GAP = auto()
    FIND_ROBOT2_TO_DELETE = auto()
    FOLLOW_ME_AND_DELETE = auto()
    MOVE_PAST_ROBOT2 = auto()
    MARK_START = auto()
    MOVE_HOME = auto()

class Board:
    def __init__(self, dims=(16,16)):
        """ Create a board of the dimension given """
        self.robot1 = [[7,8], STATE.SEARCHSOUTH, SOUTH]   # Start at the location in state 1, facing South
        self.robot2 = [[7,9], STATE.IDLE, SOUTH] # Start at the location in state 0, facing South
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
        points = [x + dx/2, y + 2, x + 2, y + dy/2 + 1, x + dx - 2, y + dy/2 + 1]
        
        if direction == SOUTH:
            points = [x + dx/2, y + dy - 2, x + 2, y + dy/2 - 1, x + dx - 2, y + dy/2 - 1]
        elif direction == EAST:
            points = [x + dx/2 - 2, y + 2, x + dx/2 - 2, y + dy - 2, x + dx - 2, y + dy/2]
        elif direction == WEST:
            points = [x + dx/2 + 2, y + 2, x + dx/2 + 2, y + dy - 2, x + 2, y + dy/2]
        
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
        #canvas.create_text((x+deltaX/2, y+deltaY/2), anchor='center', font=("Purisa", 14), text=str(self.robot1[1].value))
        
        u, v = self.robot2[0]
        x = offset + u*deltaX 
        y = offset + (self.height-v-1)*deltaY # Flip the y
        canvas.create_oval((x+2, y+2, x+deltaX-2, y+deltaY-2),fill="blue")
        self.DrawDirection(canvas, x, y, deltaX, deltaY, self.robot2[2])
        #canvas.create_text((x+deltaX/2, y+deltaY/2), anchor='center', font=("Purisa", 14), text=str(self.robot2[1].value))

        canvas.create_text((20,18), anchor='sw', text="{}x{}".format(self.width,self.height))
    
    def ShowResults(self, canvas, size = (400,400), offset = 20):
        steps,moves,placed,picked,data = self.results
        canvas.create_text((offset, 30), anchor='nw', font=("Purisa", 14), text="Step: {}".format(steps))
        canvas.create_text((offset, 60), anchor='nw', font=("Purisa", 14), text="Robot Moves: {}".format(moves))
        canvas.create_text((offset, 90), anchor='nw', font=("Purisa", 14), text="Tiles Placed: {}".format(placed))
        canvas.create_text((offset, 120), anchor='nw', font=("Purisa", 14), text="Tiles Removed: {}".format(picked))
        
        
        # ToDo: Fix up the states into something more like a dictionary
        canvas.create_text((offset, 180), anchor='nw', font=("Purisa", 14), text="Robot 1: {}".format(str(self.robot1[1])[6:]))
        canvas.create_text((offset, 210), anchor='nw', font=("Purisa", 14), text="Robot 2: {}".format(str(self.robot2[1])[6:]))

        
    def Generate(self):
        """ Generate the initial tile setup. """
        try:
            for i in range(MAX_MOVES): # Run out 100 steps in the sim
                self.Update()
                if self.CheckState(self.robot1, STATE.FINISH):
                    break
        except Exception as e:
            print("Something bad happened here!")
            print(e)
            
        self.SetStep(0) # Go back to the beginning
        
    
    def Update(self):
        message = ""
        loc =  tuple(self.robot1[0])
        
        # ********************************************************************************
        # Actions for Robot#2
        # ********************************************************************************
        if self.CheckState(self.robot2, STATE.MARK_START):
            self.SetState(self.robot2, STATE.IDLE)
        elif self.CheckState(self.robot2, STATE.MOVE_HOME):            
            self.MoveRobotBackward(self.robot2)
            self.TurnRobotLeft(self.robot2)
            self.SetState(self.robot2, STATE.IDLE)        
        # ********************************************************************************
        # Start searching to the south for a place to start
        # ********************************************************************************
        if self.CheckState(self.robot1, STATE.SEARCHSOUTH): #this robot must search for bottom
            self.SearchSouth()
        # ********************************************************************************
        # After searching south look east and west for a path to continue south    
        # ********************************************************************************
        elif self.CheckState(self.robot1, STATE.SEARCH_EAST_WEST): #this robot must search for bottom by going right or left
            self.SearchEastWest()
        # ********************************************************************************            
        #
        # ********************************************************************************
        elif self.CheckState(self.robot1, STATE.BUILDINGBB): # We are building the Bounding box
            if self.IsRightEmpty(self.robot1) and self.IsLeftEmpty(self.robot1) and self.IsForwardEmpty(self.robot1):
                self.TurnRobotRight(self.robot1)
                self.MoveRobotForward(self.robot1)
                self.PlaceTile(loc) # Place a tile on the square that I left
                self.SetState(self.robot1,STATE.FORGEAHEAD_2)
            else:
                if not self.IsForwardEmpty(self.robot1):
                    self.MoveRobotForward(self.robot1)
                    self.SetState(self.robot1, STATE.TILE_MEMBERSHIP_CHEAPCHECK) #Start to figure out what we are doing
                elif not self.IsRightEmpty(self.robot1): # We see something, on the right
                    self.TurnRobotRight(self.robot1)
                    self.MoveRobotForward(self.robot1)
                    self.SetState(self.robot1, STATE.TILE_MEMBERSHIP_CHEAPCHECK) # ToDo: Should this be a different state since we turned before moving?
                    #self.SetState(self.robot1, STATE.SHIFT_BEGIN)
                else: # There is something to the left
                    self.SetState(self.robot1, STATE.BACKTRACK)
                    
        # ********************************************************************************
        #
        # ********************************************************************************
        elif self.CheckState(self.robot1, STATE.SHIFT_BEGIN):
            #self.MoveRobotBackward(self.robot1)
            if not self.IsLeftEmpty(self.robot1):
                self.MoveRobotBackward(self.robot1)
                self.SetState(self.robot1, STATE.BACKTRACK)
            else:
                self.PlaceTile(loc) # ToDo: Confirm that this is alright
                self.SetState(self.robot1, STATE.SHIFT_PICK_BLOCK)
        # ********************************************************************************
        #
        # ********************************************************************************
        elif self.CheckState(self.robot1, STATE.SHIFT_PICK_BLOCK):
            if self.IsBackwardEmpty(self.robot1): # ToDo: Revisit this if the shifting changes!
                self.TurnRobotLeft(self.robot1)
                self.SetState(self.robot1, STATE.FOLLOWBB_CW)
            else:
                self.MoveRobotBackward(self.robot1)
                self.RemoveTile(loc)
                self.TurnRobotLeft(self.robot1)
                self.SetState(self.robot1, STATE.SHIFT_VALIDATE_PLACEMENT)
        # ********************************************************************************
        #
        # ********************************************************************************
        elif self.CheckState(self.robot1, STATE.SHIFT_VALIDATE_PLACEMENT):             
                self.MoveRobotForward(self.robot1)
                if self.IsForwardEmpty(self.robot1):# and not self.IsLeftEmpty(self.robot1):
                    self.SetState(self.robot1, STATE.SHIFT_CONTINUE) 
                else:
                    self.MoveRobotBackward(self.robot1)
                    self.TurnRobotRight(self.robot1)
                    self.SetState(self.robot1, STATE.SHIFT_UNDO)
        # ********************************************************************************
        #
        # ********************************************************************************
        elif self.CheckState(self.robot1, STATE.SHIFT_UNDO):
            self.MoveRobotForward(self.robot1)
            if self.IsLeftEmpty(self.robot1):
                self.SetState(self.robot1, STATE.BACKTRACK)
            else:
                self.PlaceTile(tuple(self.robot1[0])) # Place the tile in the space adjacent to the roobot then move onto it
                locLeft = self.GetLocation(self.robot1, COUNTERCLOCKWISE[self.robot1[2]])
                self.RemoveTile(locLeft)
        # ********************************************************************************
        #
        # ********************************************************************************
        elif self.CheckState(self.robot1, STATE.SHIFT_CONTINUE):
            if self.IsLeftEmpty(self.robot1):
                self.MoveRobotBackward(self.robot1)
                self.PlaceTile(loc)
                self.TurnRobotRight(self.robot1)
                self.SetState(self.robot1, STATE.SHIFT_PICK_BLOCK)
            else:
                self.MoveRobotBackward(self.robot1)
                self.TurnRobotRight(self.robot1)
                self.SetState(self.robot1, STATE.SHIFT_UNDO)

        # ********************************************************************************
        #
        # ********************************************************************************            
        elif self.CheckState(self.robot1, STATE.FORGEAHEAD_0): # Move forward after a turn to the right
            if self.IsRightEmpty(self.robot1) and self.IsLeftEmpty(self.robot1) and self.IsForwardEmpty(self.robot1):
                self.MoveRobotForward(self.robot1)
                self.PlaceTile(loc) # Place a tile on the square that I left
                self.SetState(self.robot1,STATE.BUILDINGBB)
            else:
                if not self.IsForwardEmpty(self.robot1):
                    self.SetState(self.robot1, STATE.TILE_MEMBERSHIP_CHEAPCHECK) #Start to figure out what we are doing
                    self.MoveRobotForward(self.robot1)
                else:
                    self.SetState(self.robot1, STATE.BACKTRACK)
        # ********************************************************************************
        #
        # ********************************************************************************
        elif self.CheckState(self.robot1, STATE.FORGEAHEAD_1): # Move forward after a turn to the right
            if self.Look4TileRight(self.robot1) and self.IsLeftEmpty(self.robot1) and self.IsForwardEmpty(self.robot1):
                self.MoveRobotForward(self.robot1)
                self.PlaceTile(loc) # Place a tile on the square that I left
                self.SetState(self.robot1,STATE.FORGEAHEAD_0)
            else:
                if not self.IsForwardEmpty(self.robot1) and self.IsLeftEmpty(self.robot1) and self.IsRightEmpty(self.robot1):
                    self.SetState(self.robot1, STATE.TILE_MEMBERSHIP_CHEAPCHECK) #Start to figure out what we are doing
                    self.MoveRobotForward(self.robot1)
                else:
                    self.SetState(self.robot1, STATE.BACKTRACK)
        # ********************************************************************************
        #
        # ********************************************************************************
        elif self.CheckState(self.robot1, STATE.FORGEAHEAD_2): # Move forward after a turn to the right
            if self.Look4TileRight(self.robot1) and self.IsLeftEmpty(self.robot1) and self.IsForwardEmpty(self.robot1):
                self.MoveRobotForward(self.robot1)
                self.PlaceTile(loc) # Place a tile on the square that I left
                self.SetState(self.robot1,STATE.FORGEAHEAD_1)
            else:
                if not self.IsForwardEmpty(self.robot1):
                    self.SetState(self.robot1, STATE.TILE_MEMBERSHIP_CHEAPCHECK) #Start to figure out what we are doing
                    self.MoveRobotForward(self.robot1)
                else:
                    self.SetState(self.robot1, STATE.BACKTRACK)
        # ********************************************************************************
        #
        # ********************************************************************************
        elif self.CheckState(self.robot1, STATE.TILE_MEMBERSHIP_CHEAPCHECK): # Step on to the tile ahead and do the cheap check
            if self.LookForRobot():
                if self.IsRobot1BehindRobot2(): 
                    self.MoveRobotBackward(self.robot1) # On the Polyomino
                    self.SetState(self.robot1, STATE.SHIFT_BEGIN)
                else:
                    if self.IsRobot2AtRightOfRobot1():
                        locBack = self.GetLocation(self.robot1, BEHIND[self.robot1[2]])
                        self.PlaceTile(locBack) # Place a tile on the square that I left
                        self.SetState(self.robot1, STATE.FINISH)
                    # if Robot1 came from below, there is
                    elif self.IsRobot2FacingRobot1(): # ToDo: FIX THIS PLEASE, TOO MUCH GOING ON
                        self.MoveRobotBackward(self.robot1)
                        self.RemoveTile(loc)
                        self.MoveRobotForward(self.robot2)
                        self.TurnRobotRight(self.robot2)
                        self.SetState(self.robot1, STATE.PEPARE_2_SHIFT_LEFT)
                    else:
                        pass # We need to do some shifting to fix this
            elif self.CountNeighbors(self.robot1) == 1:
                self.MoveRobotBackward(self.robot1)
                self.SetState(self.robot1, STATE.RETURN_2_BB)
                
            elif self.CountNeighbors(self.robot1) == 3:# this is p
                self.MoveRobotBackward(self.robot1)
                self.SetState(self.robot1, STATE.SHIFT_BEGIN)
                # This is a polyomino
            else: # Explore to determine if this is p or bb
                self.MoveRobotBackward(self.robot1)
                self.SetState(self.robot1, STATE.TILE_MEMBERSHIP_MARKER_DECISION)
                # To DO: Set the marker here and explore the polyomino
          
        # ********************************************************************************
        #
        # ********************************************************************************            
        elif self.CheckState(self.robot1, STATE.RETURN_2_BB):
            
            if not self.IsRightEmpty(self.robot1):
                self.TurnRobotLeft(self.robot1)
                self.MoveRobotBackward(self.robot1)
                self.SetState(self.robot1, STATE.SHIFT_BEGIN)
            else:
                self.MoveRobotBackward(self.robot1)
                if self.IsBackwardEmpty(self.robot1):
                    self.TurnRobotLeft(self.robot1)
                    self.SetState(self.robot1, STATE.FORGEAHEAD_1)
                else:
                    if not self.IsThisEmpty(self.robot1):
                        self.SetState(self.robot1, STATE.SHIFT_BEGIN)
                    #self.SetState(self.robot1, STATE.SHIFT_BEGIN)
        # ********************************************************************************
        #
        # ********************************************************************************            
        elif self.CheckState(self.robot1, STATE.PEPARE_2_SHIFT_LEFT):
            if self.IsRightEmpty(self.robot1): # We need to shift a column to the left
                pass
            else: # we need to turn and move forward
                self.TurnRobotLeft(self.robot1)
                self.SetState(self.robot1, STATE.SHIFT_AHEAD)
        # ********************************************************************************
        #
        # ********************************************************************************            
        elif self.CheckState(self.robot1, STATE.SHIFT_AHEAD):
            if self.IsForwardEmpty(self.robot2):
                self.PlaceTile(loc)
                self.SetState(self.robot1, STATE.FINISH)
            else:
                self.MoveRobotForward(self.robot1)
                self.PlaceTile(loc)
                self.MoveRobotForward(self.robot2)
                locBack = self.GetLocation(self.robot2, BEHIND[self.robot2[2]])
                self.RemoveTile(locBack)
                
        # ********************************************************************************
        #
        # ********************************************************************************            
        elif self.CheckState(self.robot1, STATE.TILE_MEMBERSHIP_MARKER_DECISION):            
            if self.IsBackwardEmpty(self.robot1) and not self.IsRightEmpty(self.robot1): # Don't place a marker, this is a corner
                self.SetState(self.robot1, STATE.TILE_MEMBERSHIP_SEARCH)
            elif not self.IsBackwardEmpty(self.robot1):
                self.MoveRobotBackward(self.robot1)
                if not self.IsBackwardEmpty(self.robot1): # Don't place a marker here, I came straight on
                    self.SetState(self.robot1, STATE.TILE_MEMBERSHIP_START_SEARCH)
                else:
                    self.MoveRobotBackward(self.robot1) # ToDo: Split this into 2 states!
                    self.SetState(self.robot1, STATE.TILE_MEMBERSHIP_VALIDATE_MARKER)
                    
        # ********************************************************************************
        #
        # ********************************************************************************            
        elif self.CheckState(self.robot1, STATE.TILE_MEMBERSHIP_VALIDATE_MARKER):
            if self.IsLeftEmpty(self.robot1): # and self.IsBackwardEmpty(self.robot1):
                self.MoveRobotForward(self.robot1)
                self.PlaceTile(loc)
                self.SetState(self.robot1,STATE.TILE_MEMBERSHIP_START_SEARCH)
            else:
                self.MoveRobotForward(self.robot1)
                self.TurnRobotLeft(self.robot1)
                self.SetState(self.robot1, STATE.BACKTRACK)
        
        # ********************************************************************************
        #
        # ********************************************************************************            
        elif self.CheckState(self.robot1, STATE.TILE_MEMBERSHIP_START_SEARCH):
            self.MoveRobotForward(self.robot1)
            self.SetState(self.robot1, STATE.TILE_MEMBERSHIP_SEARCH)
        # ********************************************************************************
        #
        # ********************************************************************************            
        elif self.CheckState(self.robot1, STATE.TILE_MEMBERSHIP_SEARCH):
            self.MoveRobotForward(self.robot1)
            if self.LookForRobot():
                if self.IsRobot1BehindRobot2(): # we are in p
                    self.robot1[2] = self.robot2[2] # Orient robot 1 to match robot 2
                    self.TurnRobotRight(self.robot2)
                    self.MoveRobotForward(self.robot2)
                    self.SetState(self.robot1, STATE.MOVE_PAST_ROBOT2)
                else: # I am not in p
                    self.TurnRobotRight(self.robot1)
                    self.TurnRobotRight(self.robot1)
                    self.SetState(self.robot1, STATE.FOLLOWBB_CW_COMPLETE)
                    # We are below the robot
            elif not self.IsRightEmpty(self.robot1):
                self.TurnRobotRight(self.robot1)
            elif not self.IsForwardEmpty(self.robot1):
                pass
            elif not self.IsLeftEmpty(self.robot1):
                self.TurnRobotLeft(self.robot1)
            else:
                self.TurnRobotRight(self.robot1)
                self.TurnRobotRight(self.robot1)

        # ********************************************************************************
        #
        # ********************************************************************************            
        elif self.CheckState(self.robot1, STATE.MOVE_PAST_ROBOT2):
            self.MoveRobotForward(self.robot1)
            self.SetState(self.robot1, STATE.FOLLOWBB_CW_LOOK4MARKER)
            self.SetState(self.robot2, STATE.MOVE_HOME)


        # ********************************************************************************
        #
        # ********************************************************************************            
        elif self.CheckState(self.robot1, STATE.BACKTRACK):
            # look behind
            if self.IsBackwardEmpty(self.robot1): # See if there is a tile behind me
                self.TurnRobotLeft(self.robot1)
                self.SetState(self.robot1, STATE.CHECKFORWARD)
            else:
                if self.IsRobot2BehindRobot1(): # We backed into Robot 2!
                    self.MoveRobotForward(self.robot1)
                    self.RemoveTile(loc)
                    self.MoveRobotForward(self.robot2)
                    self.SetState(self.robot1, STATE.BRIDGE)
                else:
                    self.MoveRobotBackward(self.robot1)
                    self.RemoveTile(loc)
        # ********************************************************************************
        #
        # ********************************************************************************                
        elif self.CheckState(self.robot1, STATE.BRIDGE):
            if self.IsForwardEmpty(self.robot1):
                self.MoveRobotForward(self.robot1)
                self.MoveRobotForward(self.robot2)
            else:
                self.MoveRobotForward(self.robot1)
                self.MoveRobotForward(self.robot2)
                self.SetState(self.robot1, STATE.SEARCHSOUTH)
        
        # ********************************************************************************
        #
        # ********************************************************************************                
        elif self.CheckState(self.robot1, STATE.CHECKFORWARD):
            if self.IsForwardEmpty(self.robot1): # if the square ahead is open
                self.MoveRobotForward(self.robot1)
                self.SetState(self.robot1, STATE.BUILDINGBB)
            else:
                self.SetState(self.robot1, STATE.BACKTRACK)
                
                
        # ********************************************************************************
        #
        # ********************************************************************************                
        elif self.CheckState(self.robot1, STATE.FOLLOWBB_CW_LOOK4MARKER):
            if not self.IsForwardEmpty(self.robot1):
                self.MoveRobotForward(self.robot1)
            elif not self.IsRightEmpty(self.robot1):
                self.TurnRobotRight(self.robot1)
                self.MoveRobotForward(self.robot1)
            elif not self.IsLeftEmpty(self.robot1):
                locLeft = self.GetLocation(self.robot1, COUNTERCLOCKWISE[self.robot1[2]])
                self.RemoveTile(locLeft)
                #locAhead = self.GetLocation(self.robot1, self.robot1[2])
                #self.PlaceTile(locAhead) # Place a tile on the square that I left
                self.SetState(self.robot1, STATE.FORGEAHEAD_1)
                #self.SetState(self.robot1, STATE.CHECKFORWARD)
            else:
                self.MoveRobotForward(self.robot1)
                if self.IsLeftEmpty(self.robot1): 
                    self.PlaceTile(tuple(self.robot1[0])) # Place the tile in the space where the robot now is
                self.SetState(self.robot1, STATE.SHIFT_BEGIN)
        # ********************************************************************************
        #
        # ********************************************************************************                
        elif self.CheckState(self.robot1, STATE.FOLLOWBB_CW_COMPLETE):
            if not self.IsForwardEmpty(self.robot1):
                self.MoveRobotForward(self.robot1)
            elif not self.IsRightEmpty(self.robot1):
                self.TurnRobotRight(self.robot1)
                self.MoveRobotForward(self.robot1)
            else:
                self.MoveRobotForward(self.robot1)
                # To Do: Chec here to see if a shif is needed to the left
                print("Stepped into the gap")
                IsForwardEmpty = list(map(add, self.robot1[0], MOVES[self.robot1[2]]))
                if self.CheckCorrnerTile(IsForwardEmpty): # We are at a corner, proceed
                    self.PlaceTile(tuple(self.robot1[0])) # Place the tile in the space where the robot now is
                    self.SetState(self.robot1, STATE.CLOSE_THE_GAP)
                else: # We are not on a coner, shift to find one
                    self.PlaceTile(tuple(self.robot1[0])) # Place the tile in the space where the robot now is
                    self.SetState(self.robot1, STATE.SHIFT_AND_CLOSE)
        
        # ********************************************************************************
        #
        # ********************************************************************************         
        elif self.CheckState(self.robot1, STATE.SHIFT_AND_CLOSE):
            if self.IsBackwardEmpty(self.robot1):
                self.TurnRobotLeft(self.robot1)
                self.SetState(self.robot1, STATE.FOLLOWBB_CW_COMPLETE)
                print("Look for a corner again!")
            else:
                self.MoveRobotBackward(self.robot1)
                self.RemoveTile(loc)
                self.TurnRobotLeft(self.robot1)
                IsForwardEmpty = tuple(map(add, self.robot1[0], MOVES[self.robot1[2]]))
                self.PlaceTile(IsForwardEmpty) # Place
                self.TurnRobotRight(self.robot1)
                print("Keep Shifting")
        # ********************************************************************************
        #
        # ********************************************************************************                
        elif self.CheckState(self.robot1, STATE.CLOSE_THE_GAP):
            self.MoveRobotForward(self.robot1)
            self.TurnRobotRight(self.robot1)
            self.SetState(self.robot1, STATE.FIND_ROBOT2_TO_DELETE)
        
        # ********************************************************************************
        #
        # ********************************************************************************                
        elif self.CheckState(self.robot1, STATE.FIND_ROBOT2_TO_DELETE):
            self.MoveRobotForward(self.robot1)
            if self.LookForRobot():
                self.TurnRobotRight(self.robot1)
                self.TurnRobotRight(self.robot1)
                self.robot2[2] = self.robot1[2] # Share the orientation
                self.SetState(self.robot1, STATE.FOLLOW_ME_AND_DELETE)
        
        # ********************************************************************************
        #
        # ********************************************************************************                
        elif self.CheckState(self.robot1, STATE.FOLLOW_ME_AND_DELETE):
            self.MoveRobotForward(self.robot1)
            self.MoveRobotForward(self.robot2)
            self.RemoveTile(loc)
            if self.IsForwardEmpty(self.robot1): # I reached the end
                self.SetState(self.robot1, STATE.FINISH)
            # To Do: Fix this up
        
        # ********************************************************************************
        #
        # ********************************************************************************                
        elif self.CheckState(self.robot1, STATE.FOLLOWBB_CW):
            if not self.IsForwardEmpty(self.robot1):
                self.MoveRobotForward(self.robot1)
            elif not self.IsRightEmpty(self.robot1):
                self.TurnRobotRight(self.robot1)
                self.MoveRobotForward(self.robot1)
            else:
                self.MoveRobotForward(self.robot1)
                self.SetState(self.robot1, STATE.FORGEAHEAD_0)
        
        self.LogResults(message) # Log the results of the operation
        

    def LogResults(self,message):
        if self.robot1[1] in [STATE.IDLE, STATE.SEARCHSOUTH, STATE.SEARCH_EAST_WEST]: # Initial Search States
            self.results[4][0] +=1
        if self.robot1[1] in [STATE.BUILDINGBB, STATE.FORGEAHEAD_0, STATE.SHIFT_BEGIN, 
                      STATE.SHIFT_PICK_BLOCK, STATE.SHIFT_CONTINUE, STATE.SHIFT, STATE.CLOSE_THE_GAP,
                      STATE.SHIFT_AND_CLOSE, STATE.TILE_MEMBERSHIP_MARKER_DECISION]: # Building/Shifting States
            self.results[4][1] +=1
        if self.robot1[1] in [STATE.SHIFT_UNDO, STATE.BACKTRACK, STATE.FOLLOW_ME_AND_DELETE]: # Delete States
            self.results[4][2] +=1
        if self.robot1[1] in [STATE.FOLLOWBB_CW, STATE.FOLLOWBB_CW_LOOK4MARKER, STATE.CHECKFORWARD, 
                      STATE.FOLLOWBB_CW_COMPLETE, STATE.TILE_MEMBERSHIP_CHEAPCHECK, 
                      STATE.TILE_MEMBERSHIP_START_SEARCH, STATE.TILE_MEMBERSHIP_SEARCH, 
                      STATE.FIND_ROBOT2_TO_DELETE, STATE.MOVE_PAST_ROBOT2]: # Move/SearchBB States
            self.results[4][3] +=1
        
        self.log.LogState(self.tiles, self.robot1, self.robot2, " ", list(self.results))


#STATE.FINISH = 10 # Do nothing here

    def ComputeDims(self,preference):
        minimum = preference + 8 # To ensure andquate space 
        result = 2**math.ceil(math.log2(minimum))
        return (result, result)

    def SetPolyomino(self, poly="??"):
        self.tiles.fill(0)
        start1 = [7,8]
        start2 = [7,9]
        
        tile_set = []
        dims = (32,32)
                
        if poly == "single":
            start1 = [4,4]
            start2 = [4,5]
            self.tiles[4,4] = 1
            dims = (8,8)
        elif poly == "spiral!":
            tile_set = [(7,8), (7,9), (7,10), (6,10), (5,10), (5,9), (5,8), (5,7), (5,6),
                        (5,5), (6,5), (7,5), (8,5), (9,5), (9,6), (9,7), (9,8), (9,9)]
            dims = (16,16)
        elif poly[0] == "L":
            size = int(poly[1:])
            tile_set = [(4,4)]
            for i in range(1,size):
                tile_set.append((4+i ,4))
                tile_set.append((4, 4+i))
            start1 = [4,4]
            start2 = [4,5]
            dims = self.ComputeDims(size)
        elif poly[0] == "U":
            size = int(poly[1:])
            tile_set = [(4,4)]
            for i in range(1,size):
                tile_set.append((4+i ,4))
                tile_set.append((4, 4+i))
                tile_set.append((4+size-1, 4+i))
            start1 = [4,4]
            start2 = [4,5]
            dims = self.ComputeDims(size)
        elif poly[0] == "C":
            size = int(poly[1:])
            tile_set = [(4,4)]
            for i in range(1,size):
                tile_set.append((4+i ,4))
                tile_set.append((4, 4+i))
                tile_set.append((4+i, 4+size-1))
            start1 = [4,4]
            start2 = [4,5]
            dims = self.ComputeDims(size)
        elif poly[0] == "n":
            size = int(poly[1:])
            tile_set = []
            for i in range(size):
                tile_set.append((4+i ,4+size-1))
                tile_set.append((4, 4+i))
                tile_set.append((4+size-1, 4+i))
            start1 = [4,4]
            start2 = [4,5]
            dims = self.ComputeDims(size)
        elif poly[:2] == "SQ":
            size = int(poly[2:])
            tile_set = []
            for i in range(size):
                for j in range(size):
                    tile_set.append((4+i ,4+j))
            start1 = [4,4]
            start2 = [4,5]
            dims = self.ComputeDims(size)
        elif poly[0] ==  u"\uA73E":
            size = int(poly[1:])
            tile_set = []
            for i in range(size):
                tile_set.append((4+i ,4+size-1))
                tile_set.append((4+i, 4))
                tile_set.append((4+size-1, 4+i))
            start1 = [4,4]
            start2 = [4,5]
            dims = self.ComputeDims(size)
        elif poly == "smallHook":
            tile_set = [(7,10), (7,9), (7,8), (7,7), (7,6), (8,6), (9,6), (10,6), (11,6),
                        (11,11), (12,11), (12,10), (12,9), (12,8), (12,7), (12,6)]
            dims = (20,20)
        elif poly == "MY_UH":
            tile_set = [(3,12), (3,11), (3,10), (3,9), (3,8), (3,7), (4,7), (5,7), (6,7),
                        (7,7), (7,8), (7,9), (7,10), (7,11), (7,12), # H
                        (5,9), (5,8), (5,6), (5,5), (5,4), (5,3), (5,2), (6,5), (7,5),
                        (8,5), (9,5), (9,6), (9,7), (9,8), (9,9), (9,4), (9,3), (9,2)]
            dims = (16,16)
        elif poly == "backwardsC":
            tile_set = [(7,9), (7,8), (8,9), (9,9), (9,8), (9,7), (9,6), (9,5), (9,4),
                        (8,4), (7,4)]
            dims = (16,16)
        elif poly == "hookedN":
            tile_set = [(7,9), (7,8), (8,9), (9,9), (10,9), (10,8), (10,7), (10,6), (10,5),
                        (10,4), (9,4), (8,4)]
            dims = (16,16)
        elif poly == "leggyN":
            tile_set = [(7,9), (7,8), (8,9), (9,9), (10,9), (10,8), (10,7)]
            dims = (16,16)
        elif poly == "NASAsq":
            dims = (64,64)
            tile_set = [(3, 20), (4, 20), (5, 20), (6, 20), (7, 20), (8, 20), (9, 20), (10, 20), (11, 20), (12, 20), (13, 20), (14, 20), (15, 20), (16, 20), (17, 20), (18, 20), (19, 20), (20, 20), (21, 20), (22, 20), (23, 20), (24, 20), (25, 20), (26, 20), (27, 20), (28, 20), (29, 20), (30, 20), (31, 20), (32, 20), (33, 20), (34, 20), (35, 20), (36, 20), (37, 20), (38, 20), (39, 20), (40, 20), (41, 20), (42, 20), (43, 20), (44, 20), (45, 20), (46, 20), (47, 20), (3, 19), (47, 19), (3, 18), (6, 18), (7, 18), (8, 18), (9, 18), (13, 18), (14, 18), (20, 18), (21, 18), (28, 18), (29, 18), (30, 18), (31, 18), (32, 18), (33, 18), (40, 18), (41, 18), (47, 18), (3, 17), (5, 17), (6, 17), (7, 17), (8, 17), (9, 17), (10, 17), (13, 17), (14, 17), (19, 17), (20, 17), (21, 17), (22, 17), (27, 17), (28, 17), (29, 17), (30, 17), (31, 17), (32, 17), (33, 17), (34, 17), (39, 17), (40, 17), (41, 17), (42, 17), (47, 17), (3, 16), (5, 16), (6, 16), (9, 16), (10, 16), (13, 16), (14, 16), (18, 16), (19, 16), (20, 16), (21, 16), (22, 16), (23, 16), (27, 16), (28, 16), (38, 16), (39, 16), (40, 16), (41, 16), (42, 16), (43, 16), (47, 16), (3, 15), (5, 15), (6, 15), (9, 15), (10, 15), (13, 15), (14, 15), (18, 15), (19, 15), (22, 15), (23, 15), (27, 15), (28, 15), (38, 15), (39, 15), (42, 15), (43, 15), (47, 15), (3, 14), (5, 14), (6, 14), (9, 14), (10, 14), (13, 14), (14, 14), (18, 14), (19, 14), (22, 14), (23, 14), (27, 14), (28, 14), (38, 14), (39, 14), (42, 14), (43, 14), (47, 14), (3, 13), (5, 13), (6, 13), (9, 13), (10, 13), (13, 13), (14, 13), (17, 13), (18, 13), (19, 13), (22, 13), (23, 13), (24, 13), (27, 13), (28, 13), (29, 13), (30, 13), (31, 13), (32, 13), (33, 13), (37, 13), (38, 13), (39, 13), (42, 13), (43, 13), (44, 13), (47, 13), (3, 12), (5, 12), (6, 12), (9, 12), (10, 12), (13, 12), (14, 12), (17, 12), (18, 12), (23, 12), (24, 12), (28, 12), (29, 12), (30, 12), (31, 12), (32, 12), (33, 12), (34, 12), (37, 12), (38, 12), (43, 12), (44, 12), (47, 12), (3, 11), (5, 11), (6, 11), (9, 11), (10, 11), (13, 11), (14, 11), (17, 11), (18, 11), (19, 11), (20, 11), (21, 11), (22, 11), (23, 11), (24, 11), (33, 11), (34, 11), (37, 11), (38, 11), (39, 11), (40, 11), (41, 11), (42, 11), (43, 11), (44, 11), (47, 11), (3, 10), (5, 10), (6, 10), (9, 10), (10, 10), (13, 10), (14, 10), (16, 10), (17, 10), (18, 10), (19, 10), (20, 10), (21, 10), (22, 10), (23, 10), (24, 10), (25, 10), (33, 10), (34, 10), (36, 10), (37, 10), (38, 10), (39, 10), (40, 10), (41, 10), (42, 10), (43, 10), (44, 10), (45, 10), (47, 10), (3, 9), (5, 9), (6, 9), (9, 9), (10, 9), (13, 9), (14, 9), (16, 9), (17, 9), (24, 9), (25, 9), (33, 9), (34, 9), (36, 9), (37, 9), (44, 9), (45, 9), (47, 9), (3, 8), (5, 8), (6, 8), (9, 8), (10, 8), (11, 8), (12, 8), (13, 8), (14, 8), (16, 8), (17, 8), (24, 8), (25, 8), (27, 8), (28, 8), (29, 8), (30, 8), (31, 8), (32, 8), (33, 8), (34, 8), (36, 8), (37, 8), (44, 8), (45, 8), (47, 8), (3, 7), (5, 7), (6, 7), (10, 7), (11, 7), (12, 7), (13, 7), (16, 7), (17, 7), (24, 7), (25, 7), (28, 7), (29, 7), (30, 7), (31, 7), (32, 7), (33, 7), (36, 7), (37, 7), (44, 7), (45, 7), (47, 7), (3, 6), (47, 6)]
        elif poly == "NASA":
            dims = (64,64)
            tile_set = [(5, 7), (5, 8), (5, 9), (5, 10), (5, 11), (5, 12), (5, 13), (5,  14), (5, 15), (5, 16), (5, 17), (6, 7), (6, 8), (6, 9), (6, 10), (6, 11), (6, 12), (6, 13), (6, 14), (6, 15), (6, 16), (6, 17), (6, 18), (7, 17), (7, 18), (8, 17), (8, 18), (9, 8), (9,  9), (9, 10), (9, 11), (9, 12), (9, 13), (9, 14), (9, 15), (9, 16), (9, 17), (9, 18), (10, 7), (10, 8), (10, 9), (10, 10), (10, 11), (10, 12), (10, 13), (10, 14), (10, 15), (10, 16), (10, 17), (11, 7), (11, 8), (12, 7), (12, 8), (13, 7), (13, 8), (13,  9), (13, 10), (13, 11), (13, 12), (13, 13), (13, 14), (13,  15), (13, 16), (13, 17), (13, 18), (14, 8), (14, 9), (14, 10), (14, 11), (14, 12), (14, 13), (14, 14), (14, 15), (14, 16), (14, 17), (14, 18), (16, 7), (16, 8), (16, 9), (16, 10), (17, 7), (17,  8), (17, 9), (17, 10), (17, 11), (17, 12), (17, 13), (18, 10), (18,11), (18, 12), (18, 13), (18, 14), (18, 15), (18, 16), (19, 10), (19, 11), (19, 13), (19, 14), (19, 15), (19, 16), (19, 17), (20, 10), (20, 11), (20, 16), (20, 17), (20, 18), (21, 10), (21, 11), (21, 16), (21, 17), (21, 18), (22, 10), (22, 11), (22, 13), (22, 14), (22, 15), (22, 16), (22, 17), (23, 10), (23, 11), (23, 12), (23, 13), (23, 14), (23, 15), (23, 16), (24, 7), (24, 8), (24, 9), (24, 10), (24, 11), (24, 12), (24, 13), (25, 7), (25, 8), (25, 9), (25, 10), (27, 8), (27, 13), (27, 14), (27, 15), (27, 16), (27, 17), (28, 7), (28, 8), (28, 12), (28, 13), (28, 14), (28, 15), (28, 16), (28, 17), (28, 18), (29, 7), (29, 8), (29, 12), (29, 13), (29, 17), (29, 18), (30, 7), (30,  8), (30, 12), (30, 13), (30, 17), (30, 18), (31, 7), (31, 8), (31, 12), (31, 13), (31, 17), (31, 18), (32, 7), (32, 8), (32, 12), (32, 13), (32, 17), (32, 18), (33, 7), (33, 8), (33, 9), (33, 10), (33,11), (33, 12), (33, 13), (33, 17), (33, 18), (34, 8), (34, 9), (34, 10), (34, 11), (34, 12), (34, 17), (36, 7), (36, 8), (36, 9), (36, 10), (37, 7), (37, 8), (37, 9), (37, 10), (37, 11), (37, 12), (37, 13), (38, 10), (38, 11), (38, 12), (38, 13), (38, 14), (38, 15), (38, 16), (39, 10), (39, 11), (39, 13), (39,  14), (39, 15), (39, 16), (39, 17), (40, 10), (40, 11), (40, 16), (40, 17), (40, 18), (41, 10), (41, 11), (41, 16), (41, 17), (41, 18), (42, 10), (42, 11), (42, 13), (42, 14), (42, 15), (42, 16), (42, 17), (43, 10), (43, 11), (43, 12), (43,  13), (43, 14), (43, 15), (43, 16), (44, 7), (44, 8), (44, 9), (44, 10), (44, 11), (44, 12), (44, 13), (45, 7), (45, 8), (45, 9), (45, 10), (15, 8), (26, 8), (35, 8)]
        elif poly == "TestV":
            tile_set = [(8, 16), (15, 16), (8, 15), (14, 15), (15, 15), (8, 14), (13, 14), (14, 14), (8, 13), (13, 13), (8, 12), (13, 12), (8, 11), (12, 11), (13, 11), (8, 10), (12, 10), (8, 9), (12, 9), (8, 8), (9, 8), (10, 8), (11, 8), (12, 8)]
            start1 = [8,9]
            start2 = [8,10]
        elif poly == "Spiral":    
            tile_set = [(5, 38), (6, 38), (7, 38), (8, 38), (9, 38), (10, 38), (11, 38), (12, 38), (13, 38), (14, 38), (15, 38), (16, 38), (17, 38), (18, 38), (19, 38), (20, 38), (21, 38), (22, 38), (23, 38), (24, 38), (25, 38), (26, 38), (27, 38), (28, 38), (29, 38), (30, 38), (31, 38), (32, 38), (33, 38), (34, 38), (35, 38), (5, 37), (35, 37), (5, 36), (35, 36), (5, 35), (35, 35), (5, 34), (35, 34), (5, 33), (35, 33), (5, 32), (11, 32), (12, 32), (13, 32), (14, 32), (15, 32), (16, 32), (17, 32), (18, 32), (19, 32), (20, 32), (21, 32), (22, 32), (23, 32), (24, 32), (25, 32), (26, 32), (27, 32), (28, 32), (29, 32), (35, 32), (5, 31), (11, 31), (29, 31), (35, 31), (5, 30), (11, 30), (29, 30), (35, 30), (5, 29), (11, 29), (29, 29), (35, 29), (5, 28), (11, 28), (29, 28), (35, 28), (5, 27), (11, 27), (29, 27), (35, 27), (5, 26), (11, 26), (17, 26), (18, 26), (19, 26), (20, 26), (21, 26), (22, 26), (23, 26), (29, 26), (35, 26), (5, 25), (11, 25), (17, 25), (23, 25), (29, 25), (35, 25), (5, 24), (11, 24), (17, 24), (23, 24), (29, 24), (35, 24), (5, 23), (11, 23), (17, 23), (20, 23), (23, 23), (29, 23), (35, 23), (5, 22), (11, 22), (17, 22), (20, 22), (23, 22), (29, 22), (35, 22), (5, 21), (11, 21), (17, 21), (18, 21), (19, 21), (20, 21), (23, 21), (29, 21), (35, 21), (5, 20), (11, 20), (23, 20), (29, 20), (35, 20), (5, 19), (11, 19), (23, 19), (29, 19), (35, 19), (5, 18), (11, 18), (23, 18), (29, 18), (35, 18), (5, 17), (11, 17), (23, 17), (29, 17), (35, 17), (5, 16), (11, 16), (12, 16), (13, 16), (14, 16), (15, 16), (16, 16), (17, 16), (18, 16), (19, 16), (20, 16), (21, 16), (22, 16), (23, 16), (29, 16), (35, 16), (5, 15), (29, 15), (35, 15), (5, 14), (29, 14), (35, 14), (5, 13), (29, 13), (35, 13), (5, 12), (29, 12), (35, 12), (5, 11), (29, 11), (35, 11), (5, 10), (6, 10), (7, 10), (8, 10), (9, 10), (10, 10), (11, 10), (12, 10), (13, 10), (14, 10), (15, 10), (16, 10), (17, 10), (18, 10), (19, 10), (20, 10), (21, 10), (22, 10), (23, 10), (24, 10), (25, 10), (26, 10), (27, 10), (28, 10), (29, 10), (35, 10), (35, 9), (35, 8), (35, 7), (35, 6), (35, 5)]
            dims = (64,64)
            start1 = [18,21]
            start2 = [18,22]
        elif poly == "Temple":
            tile_set = [(5, 40), (6, 40), (7, 40), (8, 40), (9, 40), (10, 40), (11, 40), (12, 40), (13, 40), (14, 40), (15, 40), (16, 40), (17, 40), (18, 40), (19, 40), (20, 40), (21, 40), (22, 40), (23, 40), (24, 40), (25, 40), (26, 40), (27, 40), (28, 40), (29, 40), (30, 40), (31, 40), (32, 40), (33, 40), (34, 40), (35, 40), (36, 40), (37, 40), (21, 39), (21, 38), (21, 37), (21, 36), (5, 35), (6, 35), (7, 35), (8, 35), (9, 35), (10, 35), (11, 35), (12, 35), (13, 35), (14, 35), (15, 35), (16, 35), (17, 35), (18, 35), (19, 35), (20, 35), (21, 35), (22, 35), (23, 35), (24, 35), (25, 35), (26, 35), (27, 35), (28, 35), (29, 35), (30, 35), (31, 35), (32, 35), (33, 35), (34, 35), (35, 35), (36, 35), (37, 35), (5, 34), (21, 34), (37, 34), (5, 33), (21, 33), (37, 33), (5, 32), (21, 32), (37, 32), (5, 31), (21, 31), (37, 31), (5, 30), (21, 30), (37, 30), (5, 29), (21, 29), (37, 29), (5, 28), (21, 28), (37, 28), (5, 27), (21, 27), (37, 27), (5, 26), (21, 26), (37, 26), (5, 25), (21, 25), (37, 25), (5, 24), (21, 24), (37, 24), (5, 23), (21, 23), (37, 23), (5, 22), (21, 22), (37, 22), (5, 21), (21, 21), (37, 21), (5, 20), (37, 20), (5, 19), (37, 19), (5, 18), (37, 18), (5, 17), (37, 17), (5, 16), (37, 16), (5, 15), (37, 15), (5, 14), (37, 14), (5, 13), (37, 13), (5, 12), (37, 12), (5, 11), (37, 11), (5, 10), (37, 10), (5, 9), (37, 9), (5, 8), (37, 8), (5, 7), (37, 7), (5, 6), (37, 6), (5, 5), (6, 5), (7, 5), (8, 5), (9, 5), (10, 5), (11, 5), (12, 5), (13, 5), (14, 5), (15, 5), (16, 5), (17, 5), (18, 5), (19, 5), (20, 5), (21, 5), (22, 5), (23, 5), (24, 5), (25, 5), (26, 5), (27, 5), (28, 5), (29, 5), (30, 5), (31, 5), (32, 5), (33, 5), (34, 5), (35, 5), (36, 5), (37, 5)]
            dims = (64,64)
            start1 = [21,22]
            start2 = [21,23]
        elif poly == "Shrine":
            tile_set = [(5, 22), (6, 22), (7, 22), (8, 22), (9, 22), (10, 22), (11, 22), (12, 22), (13, 22), (14, 22), (15, 22), (16, 22), (17, 22), (18, 22), (19, 22), (20, 22), (21, 22), (13, 21), (13, 20), (5, 19), (6, 19), (7, 19), (8, 19), (9, 19), (10, 19), (11, 19), (12, 19), (13, 19), (14, 19), (15, 19), (16, 19), (17, 19), (18, 19), (19, 19), (20, 19), (21, 19), (5, 18), (13, 18), (21, 18), (5, 17), (13, 17), (21, 17), (5, 16), (13, 16), (21, 16), (5, 15), (13, 15), (21, 15), (5, 14), (13, 14), (21, 14), (5, 13), (13, 13), (21, 13), (5, 12), (21, 12), (5, 11), (21, 11), (5, 10), (21, 10), (5, 9), (21, 9), (5, 8), (21, 8), (5, 7), (21, 7), (5, 6), (21, 6), (5, 5), (6, 5), (7, 5), (8, 5), (9, 5), (10, 5), (11, 5), (12, 5), (13, 5), (14, 5), (15, 5), (16, 5), (17, 5), (18, 5), (19, 5), (20, 5), (21, 5)]
            start1 = [13,15]
            start2 = [13,16]
        elif poly == "IEEE":
            tile_set = [(5, 18), (6, 18), (7, 18), (8, 18), (9, 18), (10, 18), (11, 18), (12, 18), (13, 18), (14, 18), (15, 18), (16, 18), (17, 18), (18, 18), (19, 18), (20, 18), (21, 18), (22, 18), (23, 18), (24, 18), (25, 18), (26, 18), (27, 18), (28, 18), (29, 18), (30, 18), (31, 18), (32, 18), (33, 18), (34, 18), (35, 18), (36, 18), (5, 17), (9, 17), (18, 17), (27, 17), (36, 17), (5, 16), (9, 16), (18, 16), (27, 16), (36, 16), (5, 15), (9, 15), (13, 15), (14, 15), (15, 15), (16, 15), (17, 15), (18, 15), (22, 15), (23, 15), (24, 15), (25, 15), (26, 15), (27, 15), (31, 15), (32, 15), (33, 15), (34, 15), (35, 15), (36, 15), (5, 14), (9, 14), (13, 14), (14, 14), (15, 14), (16, 14), (17, 14), (18, 14), (22, 14), (23, 14), (24, 14), (25, 14), (26, 14), (27, 14), (31, 14), (32, 14), (33, 14), (34, 14), (35, 14), (36, 14), (5, 13), (9, 13), (13, 13), (14, 13), (15, 13), (16, 13), (17, 13), (18, 13), (22, 13), (23, 13), (24, 13), (25, 13), (26, 13), (27, 13), (31, 13), (32, 13), (33, 13), (34, 13), (35, 13), (36, 13), (5, 12), (9, 12), (18, 12), (27, 12), (36, 12), (5, 11), (9, 11), (18, 11), (27, 11), (36, 11), (5, 10), (9, 10), (13, 10), (14, 10), (15, 10), (16, 10), (17, 10), (18, 10), (22, 10), (23, 10), (24, 10), (25, 10), (26, 10), (27, 10), (31, 10), (32, 10), (33, 10), (34, 10), (35, 10), (36, 10), (5, 9), (9, 9), (13, 9), (14, 9), (15, 9), (16, 9), (17, 9), (18, 9), (22, 9), (23, 9), (24, 9), (25, 9), (26, 9), (27, 9), (31, 9), (32, 9), (33, 9), (34, 9), (35, 9), (36, 9), (5, 8), (9, 8), (13, 8), (14, 8), (15, 8), (16, 8), (17, 8), (18, 8), (22, 8), (23, 8), (24, 8), (25, 8), (26, 8), (27, 8), (31, 8), (32, 8), (33, 8), (34, 8), (35, 8), (36, 8), (5, 7), (9, 7), (18, 7), (27, 7), (36, 7), (5, 6), (9, 6), (18, 6), (27, 6), (36, 6), (5, 5), (6, 5), (7, 5), (8, 5), (9, 5), (10, 5), (11, 5), (12, 5), (13, 5), (14, 5), (15, 5), (16, 5), (17, 5), (18, 5), (19, 5), (20, 5), (21, 5), (22, 5), (23, 5), (24, 5), (25, 5), (26, 5), (27, 5), (28, 5), (29, 5), (30, 5), (31, 5), (32, 5), (33, 5), (34, 5), (35, 5), (36, 5)]
            dims = (64,64)
            start1 = [6,6]
            start2 = [6,7]
        else:
            tile_set = [(7,8), (7,9)]
            dims = (16,16)
        
        # Establish the board state
        self.log.Reset()
        self.robot1 = [start1, STATE.SEARCHSOUTH, SOUTH]   # Start at the location in state 1, facing South
        self.robot2 = [start2, STATE.IDLE, SOUTH] # Start at the location in state 0, facing South
        self.results = [0,0,0,0,[0,0,0,0]]
        self.size = dims
        print("The size is:", self.size)
        self.width, self.height = dims
        self.tiles = np.zeros(dims, dtype=int)
        
        for point in tile_set: # set the tiles
            self.tiles[point] = 1
        
        self.LogResults("Initial Board State")
        print("Board Created")
        self.Generate()

    def SetStep(self, step):
        self.tiles.fill(0)
        tile_list, self.robot1, self.robot2, message, self.results = self.log.GetStep(step)
        self.results[0] = step
        for loc in tile_list:
            self.tiles[loc] = 1
        
        return self.robot1[1] == STATE.FINISH

            
    def SetState(self, robot, state):
        """ Set the state of the specified robot """
        robot[1] = state
    
    
    def CheckState(self, robot, state):
        return robot[1] == state

             
    def SearchSouth(self):
        """look south for another tile in P"""
        loc_south = self.GetLocation(self.robot1, SOUTH)
        
        if self.tiles[loc_south] == 1: #is a tile
            #move robot down one, state is still searching down
            self.MoveRobot(self.robot1, SOUTH)
            self.MoveRobot(self.robot2, SOUTH)
        elif self.tiles[loc_south] == 0: 
            #move robot down one, state is not searching down
            self.MoveRobot(self.robot1, SOUTH)
            self.MoveRobot(self.robot2, SOUTH)
            self.SetState(self.robot1, STATE.SEARCH_EAST_WEST) # Change the state to looking left and right
                

    def SearchEastWest(self):
        """look east and west for another tile in P"""
        loc_south = self.GetLocation(self.robot1, SOUTH)
        loc_east = self.GetLocation(self.robot1, EAST)
        loc_west = self.GetLocation(self.robot1, WEST)
        
        if self.tiles[loc_east] == 1: #is a tile
            #move right, go back to searching down
            self.MoveRobot(self.robot1, EAST)
            self.MoveRobot(self.robot2, EAST)
            self.SetState(self.robot1, STATE.SEARCHSOUTH) # Set robot1 to search for more tiles south
        elif self.tiles[loc_west] == 1: #is a tile
            #move west, go back to searching down
            self.MoveRobot(self.robot1, WEST)
            self.MoveRobot(self.robot2, WEST)
            self.SetState(self.robot1, STATE.SEARCHSOUTH) # Set robot1 to search for more tiles south
        elif self.tiles[loc_south] == 1: #is a tile
            self.MoveRobot(self.robot1, SOUTH)
            self.MoveRobot(self.robot2, SOUTH)
            self.SetState(self.robot1, STATE.SEARCHSOUTH) # Set robot1 to search for more tiles south
        else:
            self.MoveRobot(self.robot1, SOUTH)
            self.MoveRobot(self.robot2, SOUTH)
            if self.IsForwardEmpty(self.robot1):
                self.TurnRobotRight(self.robot1)
                self.SetState(self.robot1,STATE.FORGEAHEAD_1)
                self.SetState(self.robot2, STATE.MARK_START) # Get the second robot ready to move down
            else:
                self.SetState(self.robot1,STATE.SEARCHSOUTH)            
            
            
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
        #print("Look! {}".format(robot))
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
    
    def IsRobot2BehindRobot1(self):
        loc = self.GetLocation(self.robot1, BEHIND[self.robot1[2]])
        return loc == tuple(self.robot2[0])
    
    def IsRobot2AtRightOfRobot1(self):
        loc = self.GetLocation(self.robot1, CLOCKWISE[self.robot1[2]])
        return loc == tuple(self.robot2[0])
    
    def IsRobot2AtLeftOfRobot1(self):
        loc = self.GetLocation(self.robot1, COUNTERCLOCKWISE[self.robot1[2]])
        return loc == tuple(self.robot2[0])
    
    def IsRobot2FacingRobot1(self):
        loc = self.GetLocation(self.robot1, self.robot1[2])
        return loc == tuple(self.robot2[0])
    
    def IsForwardEmpty(self, robot):
        """ Returns true if the space ahead is open """
        loc = self.GetLocation(robot, robot[2])
        return self.tiles[loc] == 0
    
    def IsThisEmpty(self, robot):
        loc = tuple(robot[0])
        return self.tiles[loc] == 0
    
    
    def IsBackwardEmpty(self, robot):
        """ Returns true if the space behind the robot is open """
        loc = self.GetLocation(robot, BEHIND[robot[2]])
        return self.tiles[loc] == 0 and tuple(self.robot2[0]) != loc
    
    
    def IsLeftEmpty(self, robot):
        """ Returns true if the space to the left of the robot is open """
        loc = self.GetLocation(robot, COUNTERCLOCKWISE[robot[2]])
        return self.tiles[loc] == 0 and tuple(self.robot2[0]) != loc
    
    
    def IsRightEmpty(self, robot):
        """ Returns true if the space to the right of the robot is open """
        loc = self.GetLocation(robot, CLOCKWISE[robot[2]])
        return self.tiles[loc] == 0 and tuple(self.robot2[0]) != loc
    
    def Look4TileRight(self, robot):
        """ Returns true if there is no tile to the right of the robot """
        loc = self.GetLocation(robot, CLOCKWISE[robot[2]])
        return self.tiles[loc] == 0
    
    def CountNeighbors(self, robot):
        count = 0
        for direction in MOVES:
            loc = self.GetLocation(robot, direction)
            if self.tiles[loc] == 1:
                count += 1
        return count
    
    def GetChoices(self):
        return sorted(["single", "simpeleZ", "L2", "L3", "L4", "L5", "L6", "L7", "L8",
                        "L9", "L10", "L16", "L32", "spiral!", "smallHook", "backwardsC",
                        "hookedN", "leggyN", "MY_UH", "IEEE", "U2", "U4", "U8", "U16", "U32",
                        "C2", "C4", "C8", "C16", "C32", "n2", "n4", "n8", "n16", "n32",
                        "SQ2", "SQ4", "SQ8", "SQ16", "SQ32", u"\uA73E2", u"\uA73E4",
                        u"\uA73E8", u"\uA73E16", u"\uA73E32", "NASA", "TestV", "Spiral", "Temple", "Shrine"])
                
    def GetMoveCount(self):
        return self.log.GetStepCount()
    
