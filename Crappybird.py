import statistics
import RPi.GPIO as GPIO

import time
import adafruit_character_lcd.character_lcd_i2c as LCD
import board
import adafruit_ahtx0
#import random
from random import randint
import math
import time
from typing import List
from JoyPiNote import RGB_Matrix
from rpi_ws281x import Color
from JoypiNote_adafruit_ht16k33.segments import Seg7x4

#the board secific values
i2c = board.I2C()
lcd = LCD.Character_LCD_I2C(i2c, 16, 2, address=0x21)
segment = Seg7x4(board.I2C())
buzzer_pin = 18
touch_pin = 17
vibration_pin = 27
sensor = adafruit_ahtx0.AHTx0(i2c)
matrix = RGB_Matrix()

#the position specific values
x:int = 5 #represents the x position of the player
y:float = 5
xVelocity:float = 0
yVelocity:float = 0.1

highScore:int = 0
with open('flappyHighScore',mode='r') as handler:
    try:
        s:str = handler.read()
        highScore = int(s)
    except Exception:
        highScore = 0
ticsPerSecond:int = 100
start:bool = False

#the walls
wallMiddle:int = 0
walls:List[List[bool]] = [
    [False,False,False,False,False,False,False,False],
    [False,False,False,False,False,False,False,False],
    [False,False,False,False,False,False,False,False],
    [False,False,False,False,False,False,False,False],
    [False,False,False,False,False,False,False,False],
    [False,False,False,False,False,False,False,False],
    [False,False,False,False,False,False,False,False],
    [False,False,False,False,False,False,False,False]
]

def fillWallPixel(x:int, y:int):
    global matrix
    matrix.setPixel(position=y*8+x-1,colour=Color(100,100,100))

def onButtonPress(channel)->None:
    global start
    if(channel==touch_pin):
        if(start==False):
            start=True
        global x,y,yVelocity
        yVelocity=0.1
        y-=1

def onGameIstanceFinish():
    """
        called if the player collides with a wall
    """
    global lcd

def draw():
    """
        controlls the the 8x8 LED matrix
    """
    global matrix
    #first deactivate all lights of the matrix
    matrix.clean()
    #loop through the wall lists
    for line in range(0,8):
        for column in range(0,8):
            if(walls[line][column]==True):
                #if the bool of the wall array is true, make the LED at that Position light up
                matrix.setPixel(position=line*8+column,colour=Color(100,100,100))
    #fill the pixel where the player is
    matrix.setPixel(position=math.floor(y)*8+x-1,colour=Color(255,0,0))
    matrix.show()

#set up the button of the board so it calls 'buttonPress' if it gets pressed
GPIO.setmode(GPIO.BCM)
GPIO.setup(touch_pin, GPIO.IN, pull_up_down=GPIO.PUD_UP)
GPIO.add_event_detect(touch_pin, GPIO.RISING, callback= onButtonPress, bouncetime= 100)

GPIO.setwarnings(False)
GPIO.setmode(GPIO.BCM)

def setSegmentDisplay(input: str, clear = True):
    if clear: segment.fill(0)

    splitted = str(input)
    if len(splitted) >= 4:
        segment[0] = splitted[0]
        segment[1] = splitted[1]
        segment[2] = splitted[2]
        segment[3] = splitted[3]
    elif len(splitted) == 3:
        segment[1] = splitted[0]
        segment[2] = splitted[1]
        segment[3] = splitted[2]

    elif len(splitted) == 2:
        segment[2] = splitted[0]
        segment[3] = splitted[1]
    elif len(splitted) == 1:
        segment[3] = splitted[0]


def updatePlayerPos():
    """
        increases the players down motion and moves his position according to his down motion
    """
    global x,y,xVelocity,yVelocity
    yVelocity*=1.1
    y+=yVelocity
    matrix.setPixel(position=math.floor(y)*8+x-1,colour=Color(0,100,100))

def setNewWall():
    """
        make the walls visible according to the wallMiddle value
    """
    print(f'new wall:{wallMiddle}')
    if(wallMiddle>=2):
        walls[0][7] = True
    else:
        walls[0][7] = False
    if(wallMiddle>=3):
        walls[1][7] = True
    else:
        walls[1][7] = False
    if(wallMiddle>=4 or wallMiddle <=0):
        walls[2][7] = True
    else:
        walls[2][7] = False
    if(wallMiddle>=5 or wallMiddle <=1):
        walls[3][7] = True
    else:
        walls[3][7] = False
    if(wallMiddle>=6 or wallMiddle <=2):
        walls[4][7] = True
    else:
        walls[4][7] = False
    if(wallMiddle>=7 or wallMiddle <=3):
        walls[5][7] = True
    else:
        walls[5][7] = False
    if(wallMiddle <=4):
        walls[6][7] = True
    else:
        walls[6][7] = False
    if(wallMiddle <=5):
        walls[7][7] = True
    else:
        walls[7][7] = False


def createNewWall():
    """
        sets the right row of the wall array except a random 3 high hole to true 
    """
    global walls, wallMiddle
    #generate a random number from -2 to 2
    deltaY = randint(-2,3)
    #make sure that the new middle does not ecceed the upper and lower bound of the walls array's height
    if((wallMiddle+deltaY)<0):
        wallMiddle = 0
    elif((wallMiddle+deltaY)>7):
        wallMiddle = 7
    else:
        #offset the old wallmiddle by deltaY
        wallMiddle+=deltaY
    setNewWall()
    

    
def moveAllWalls():
    """
        goes from column 1 to 7 and sets every pixel to the value of the pixel to the left
    """
    global walls
    for line in range(0,8):
        for column in range(0,7):
            walls[line][column] = walls[line][column+1]
    
        
def loop(currentTimeStep:int)->None:
    """
        runs 'ticsPerSecond' times a second
        controlls the game flow
        
        Parameters:
        -----------
        :param int currentTimeStep: how many steps passed since the start of the programm
    """
    global x,y,matrix,lcd,ticsPerSecond
    #spawn a new wall every 3 seconds
    if(currentTimeStep%(3*ticsPerSecond)==0):
        createNewWall()
    #move the walls once a second
    if(currentTimeStep%ticsPerSecond==0):
        moveAllWalls()
        lcd.clear()
        lcd.message = f'score:{currentTimeStep}\nhighscore:{highScore}'
    #clear the most left wall column one tick after al the walls were moved so there are spaces between the walls
    if((currentTimeStep-1)%(3*ticsPerSecond)==0):
        for i in range(0,8):
            walls[i][7] = False
    #move the player 10 times a second
    if(currentTimeStep%(0.1*ticsPerSecond)==0):
        updatePlayerPos()
    draw()


def main():
    global x,y,matrix,lcd,ticsPerSecond,walls,start,highScore
    timeStep:int = 0
    lcd.message = 'willkommen zu\nCRAPPYBIRD'
    time.sleep(5)
    lcd.clear()
    lcd.message = 'Press "TOUCH"\nto start'
    while(True):
        for line in range(0,8):
            for column in range(0,8):
                walls[line][column] = False
        matrix.clean()
        time.sleep(1)
        try:
            while(start==False):
                pass
            #start the main loop
            while True:
                loop(timeStep)
                timeStep+=1
                if(math.floor(y)>7 or math.floor(y)<0):
                    break
                elif(walls[math.floor(y)][x-1]==True):
                    break
                time.sleep(1/(ticsPerSecond))
            lcd.clear()
            if(timeStep>highScore):
                highScore = timeStep
                lcd.message = f'NEUER HIGHSCORE\nscore:{highScore}'
                with open('flappyHighScore',mode='w') as handler:
                    try:
                        handler.write(str(highScore))
                    except Exception:
                        pass
            else:
                lcd.message = f'score:{timeStep}\nhighscore:{highScore}'
            timeStep=0
            y=5
        except KeyboardInterrupt:
            matrix.clean()
            time.sleep(0.3)
            GPIO.cleanup()
            lcd.message = f'score:{timeStep}\nhighscore:{highScore}'
        start=False
        
main()
