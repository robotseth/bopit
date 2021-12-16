import time
import board
import busio
import digitalio
import usb_hid
import adafruit_mpu6050
from adafruit_hid.keyboard import Keyboard
from adafruit_hid.mouse import Mouse
import ulab
import ulab.numerical

pinDict = {'b2Pin': 8, 'oPin': 14, 'gPin': 15, 'pPin': 16, 'b1Pin': 19, 'bPin':21, 'yPin':22}
keycodeDict = {'oPin': 2,'pPin': 225, 'b1Pin': 44,'yPin':1}
numDict = {1:30, 2:31, 3:32, 4:33, 5:34, 6:35, 7:36, 8:37, 9:38}
# b1 is space
# y is left click
# o is right click
# p is shift

# b2 should be toggle move/look
# g is left in inventory
# b is right in inventory

# WARNING: if the stored G and the measured G are exactly the same, it will break as infinity cannot be converted to an int

tNormal = [0.01038922699, -0.00575601491, -0.08719204983] # true normal
g = [1, 1, 1] # gravitational normal
savedG = [1, 1, 1]

timer = False
hotbarTimer = 0
hotbarTimerStarted = False
start = 0
projX = 0
projY = 0
mouseSensitivity = -15

hotbarSlot = 1
hotbarChangeMade = False

########## Toggle Walk ##########
walk = False
walkChangeMade = False
walkTimer = 0
walkTimerStarted = False

########## Move ##########
boardSensitivity = 2;

# Set up a keyboard device.
kbd = Keyboard(usb_hid.devices)

# define keyboard pins
b2Pin = digitalio.DigitalInOut(board.GP8)
b2Pin.direction = digitalio.Direction.INPUT
b2Pin.pull = digitalio.Pull.UP

oPin = digitalio.DigitalInOut(board.GP14)
oPin.direction = digitalio.Direction.INPUT
oPin.pull = digitalio.Pull.UP

gPin = digitalio.DigitalInOut(board.GP15)
gPin.direction = digitalio.Direction.INPUT
gPin.pull = digitalio.Pull.UP

pPin = digitalio.DigitalInOut(board.GP16)
pPin.direction = digitalio.Direction.INPUT
pPin.pull = digitalio.Pull.UP

b1Pin = digitalio.DigitalInOut(board.GP19)
b1Pin.direction = digitalio.Direction.INPUT
b1Pin.pull = digitalio.Pull.UP

bPin = digitalio.DigitalInOut(board.GP21)
bPin.direction = digitalio.Direction.INPUT
bPin.pull = digitalio.Pull.UP

yPin = digitalio.DigitalInOut(board.GP22)
yPin.direction = digitalio.Direction.INPUT
yPin.pull = digitalio.Pull.UP

time.sleep(0.01)  # Sleep for a bit to avoid a race condition on some systems

led = digitalio.DigitalInOut(board.LED)
led.direction = digitalio.Direction.OUTPUT

# define i2c and initial accelerometer values
i2c = busio.I2C(board.GP13, board.GP12)
mpu = adafruit_mpu6050.MPU6050(i2c)
m = Mouse(usb_hid.devices)
mX = 0
mY = 0

print("Waiting for key pin...")



def updateG():
    global timer
    global start
    global savedG
    if not yPin.value and not oPin.value:
        now = time.monotonic() # sets timer for blink without delay
        if timer == False:
            timer = True
            start = time.monotonic() # sets timer for blink without delay
        if (now - start) >= 5:
            savedG = [mpu.acceleration[0],mpu.acceleration[1],mpu.acceleration[2]]
            now = 0
            start = 0
            timer = False
    else:
        now = 0
        start = 0
        timer = False

def findTilt(): # make initial vectors unit vectors
    global projX
    global projY
    g = [mpu.acceleration[0],mpu.acceleration[1],mpu.acceleration[2]]
    unitSavedG = ulab.array(savedG) / sum(ulab.array(savedG)**2)**0.5
    unitG = ulab.array(g) / sum(ulab.array(g)**2)**0.5
    x = ulab.numerical.cross(unitSavedG,ulab.array(tNormal))
    unitX = x / sum(x**2)**0.5
    y = ulab.numerical.cross(unitSavedG,x)
    unitY = y / sum(y**2)**0.5
    projX = sum(unitG*unitX)
    projY = sum(unitG*unitY)

def hotbar():
    global hotbarSlot
    global hotbarChangeMade
    global hotbarTimer
    global hotbarTimerStarted

    if not hotbarChangeMade:
        if not gPin.value:
            hotbarSlot += 1
            hotbarChangeMade = True
        if not bPin.value:
            hotbarSlot -= 1
            hotbarChangeMade = True
        if hotbarSlot <=0:
            hotbarSlot = 9
        if hotbarSlot > 9:
            hotbarSlot = 1
    if hotbarChangeMade and not hotbarTimerStarted:
        # toggle pin
        kbd.send(29 + hotbarSlot) # test this as it used to be numDict.get(hotbarSlot)
        # set timer before next change
        hotbarTimer = time.monotonic() # sets timer for blink without delay
        hotbarTimerStarted = True
    if (time.monotonic() - hotbarTimer) >= 0.15:
        hotbarChangeMade = False
        hotbarTimerStarted = False

def toggleWalk():
    global walk
    global walkChangeMade
    global walkTimer
    global walkTimerStarted

    if not walkChangeMade:
        if not b1Pin.value:
            if walk:
                walk = False
            else:
                walk = True
            walkChangeMade = True
    if walkChangeMade and not walkTimerStarted:
        walkTimer = time.monotonic() # sets timer for blink without delay
        walkTimerStarted = True
    if (time.monotonic() - walkTimer) >= 0.2:
        walkChangeMade = False
        walkTimerStarted = False

#'w':26, 'a':4,'s':22,'d':7

"""
            kbd.press(26)
            kbd.release(22)
            
            kbd.press(4)
            kbd.release(7)
            
            kbd.press(7)
            bd.release(4)
            
            kbd.press(22)
            kbd.release(26)
            
            kbd.release(7)
            kbd.release(4)
            
            kbd.release(7)
            kbd.release(22)
"""
def move():
    global projX
    global projY
    global mouseSensitivity
    global boardSensitivity
    global walk
    if walk:
        x = int(projX*boardSensitivity)
        y = int(projY*boardSensitivity) 
        if x >= 1:
            print('a')
        elif x <= -1:
            print('s')
        else:

        if y >= 1:
            print('d')
        elif y <= -1:
            print('w')
        else:

    else:
        mX = int(projX*mouseSensitivity)
        mY = int(projY*mouseSensitivity)
        m.move(mX,mY,0) # this makes the mouse move and is disabled rn so that I can test the buttons   

while True:
    updateG() # probably needs timer work based on the hotbar function
    findTilt() # DONE
    #hotbar() # DONE
    toggleWalk()
    move()
    time.sleep(0.01)
    """
    for key in keycodeDict:
        if pinDict.get(key):
    """

    # if it is in mouse mode:
    """
    mX = int(projX*mouseSensitivity)
    mY = int(projY*mouseSensitivity)
    m.move(mX,mY,0) # this makes the mouse move and is disabled rn so that I can test the buttons
    """

    #print("Acceleration: X:%.2f, Y: %.2f, Z: %.2f m/s^2"%(mpu.acceleration))
    #print(mX)
    #print(mY)
    #print("")
    #print(mpu.acceleration)
    #time.sleep(0.001)

# key press function
# move mouse function
# toggle hotbar function -> use key press function to press the number keys