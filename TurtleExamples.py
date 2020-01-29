# -*- coding: utf-8 -*-
"""
Created on Sun Jan 26 11:54:52 2020

@author: dbied
"""


import turtle

num = int(input("Please enter a number:"))

size = 400
delta = (size/num)/2

wn = turtle.Screen()
#wn.bgcolor("lightgreen")
tess = turtle.Turtle()
#tess.color("blue")
tess.shape("blank")
tess.speed(0)
tess.pensize(3)
tess.pu()                     # this is new

#Draw the outside

tess.goto(-size,size)
tess.pd()
for i in range(4):
    tess.forward(2*size)
    tess.right(90)

tess.pu()
tess.pensize(1)

for i in range(1,num):    # start with size = 5 and grow by 2
    tess.right(90)
    x = -size + 2*size*i/(num)
    
    tess.goto(x,size)
    tess.pd()
    tess.forward(delta)
    tess.pu()

    for j in range(1,num):
        tess.pu()
        y = size - 2*size*j/(num)
        tess.goto(x,y+delta)
        tess.pd()
        tess.forward(delta)
        tess.dot()
        tess.forward(delta)
        tess.pu()
        
    tess.goto(x,-size)
    tess.pd()
    tess.backward(delta)
    tess.pu()
    
    tess.left(90)
    y = -size + 2*size*i/(num)
    tess.goto(-size, y)
    tess.pd()
    tess.forward(delta)
    tess.pu()
    
    for j in range(1,num):
        tess.pu()
        x = -size + 2*size*j/(num)
        tess.goto(x-delta,y)
        tess.pd()
        tess.forward(delta)
        tess.dot()
        tess.forward(delta)
        tess.pu()
    
    tess.goto(size, y)
    tess.pd()
    tess.backward(delta)
    tess.pu()

wn.exitonclick()