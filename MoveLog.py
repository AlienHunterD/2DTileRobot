# -*- coding: utf-8 -*-
"""
Logging module for capturing board and robot configurations as well as messages.

Dan Biediger
2019
University of Houston
"""

class MoveLog:
    
    def __init__(self):
        """ Create an empy maze of dimension given by dims """
        self.Reset()


    def Reset(self):
        self.currentStep = 0
        self.log = {}


    def LogState(self, tiles, robot1, robot2, message, results):
        tile_list = []
        width, height = tiles.shape
        # Log in all the tiles
        for v in range(height):
            for u in range(width):
                if tiles[u,v] == 1:
                    tile_list.append((u,v))
        
        self.log[self.currentStep] = (tile_list, list(robot1), list(robot2), message, results)
        self.currentStep += 1
    
    
    def GetStep(self, step):
        if step in self.log:
            return self.log[step]
        
