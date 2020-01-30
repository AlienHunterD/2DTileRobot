# -*- coding: utf-8 -*-
"""
Created on Fri Sep 20 13:23:41 2019

@author: dbied
"""

from PIL import Image
import numpy as np

OFFSET = 5

img = Image.open('test.png')

data = np.array(img.getdata())


result = []
x = 0
y = img.height -1
for item in data:
    
    if item[0] == 0:
        result.append((x+OFFSET,y+OFFSET))
    
    x +=1
    if x == img.width:
        y -= 1
        x = 0


print(result)