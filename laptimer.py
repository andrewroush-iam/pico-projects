from machine import Pin, UART, I2C, SPI

import utime, time
import _thread

i2c=I2C(0,sda=Pin(0), scl=Pin(1), freq=400000)

gpsModule = UART(1, baudrate=9600, tx=Pin(4), rx=Pin(5))
print(gpsModule)

buff = bytearray(255)

TIMEOUT = False
FIX_STATUS = False

latitude = ""
longitude = ""
home_latitude = ""
home_longitude = ""
satellites = ""


MOSI = 11
SCK = 10    
RCLK = 9

KILOBIT   = 0xFE
HUNDREDS  = 0xFD
TENS      = 0xFB
UNITS     = 0xF7
Dot       = 0x80

SEG8Code = [
    0x3F, # 0
    0x06, # 1
    0x5B, # 2
    0x4F, # 3
    0x66, # 4
    0x6D, # 5
    0x7D, # 6
    0x07, # 7
    0x7F, # 8
    0x6F, # 9
    0x77, # A
    0x7C, # b
    0x39, # C
    0x5E, # d
    0x79, # E
    0x71  # F
    ]

rclk = Pin(RCLK,Pin.OUT)
rclk(1)
spi = SPI(1)
spi = SPI(1,1000_000)
spi = SPI(1,10000_000,polarity=0, phase=0,sck=Pin(SCK),mosi=Pin(MOSI),miso=None)



def write_cmd(Num, Seg):    
    rclk(1)
    spi.write(bytearray([Num]))
    spi.write(bytearray([Seg]))
    rclk(0)
    time.sleep(0.002)
    rclk(1)

#def displayZero():
    
    
def displayTimer():
    iter = 0
    global at_home
    global in_lap
    at_home == True
    in_lap == False
    while True:
        
        if(at_home == True and in_lap == True):
            if (iter % 2 == 0):
                at_home = False
            else:
                in_lap = False
            iter = iter + 1
        
        if(at_home == True):
            write_cmd(UNITS,0x3F)
            time.sleep(0.0005)
            write_cmd(TENS,0x3F | Dot)
            time.sleep(0.0005)
            write_cmd(HUNDREDS,0x3F)
            time.sleep(0.0005)
            write_cmd(KILOBIT,0x3F | Dot)
        
        if(in_lap == True):
            #print("Current: " + str(time.ticks_ms()) + " Starttime: " + str(starttime))
            #print(starttime)
            ticks = time.ticks_diff(time.ticks_ms(), starttime)
            laptimeSeconds = int(ticks / 1000)
            laptimeMS = round(ticks/1000,2)
            write_cmd(UNITS,SEG8Code[(round(laptimeMS%1 * 10))])
            time.sleep(0.0005)
            write_cmd(TENS,SEG8Code[(round(laptimeSeconds%10))] | Dot)
            time.sleep(0.0005)
            write_cmd(HUNDREDS,SEG8Code[(round(laptimeSeconds%60 // 10))])
            time.sleep(0.0005)
            write_cmd(KILOBIT,SEG8Code[(round(laptimeSeconds%600 // 60))] | Dot)
            

        #print(starttime)

def getGPS(gpsModule):
    global FIX_STATUS, TIMEOUT, latitude, longitude
   # delay = time.ticks_ms() + 200
    utime.sleep_ms(200)
    
    while True:
            
        buff = str(gpsModule.readline())
        parts = buff.split(',')

        if (parts[0] == "b'$GPGGA" and not len(parts) < 5):
            if(parts[3] and parts[5]):
                
                latitude = convertToDegree(parts[2])
                if (parts[3] == 'S'):
                    latitude = "-" + latitude
                longitude = convertToDegree(parts[4])
                if (parts[5] == 'W'):
                    longitude = "-" + longitude
                FIX_STATUS = True
                break
       # print('reached 1 waiting for delay at')      
        break
        
        
def convertToDegree(RawDegrees):

    RawAsFloat = float(RawDegrees)
    firstdigits = int(RawAsFloat/100) 
    nexttwodigits = RawAsFloat - float(firstdigits*100) 
    
    Converted = float(firstdigits + nexttwodigits/60.0)
    Converted = '{0:.6f}'.format(Converted) 
    return str(Converted)

def atHome(latitude,longitude):
    #print("Entering atHome - lat:" + latitude + " long: " + longitude + " homelat: " + home_latitude + " homelong: " + home_longitude)
    midLat = int(float(latitude) * 1000000)
    midLong = int(float(longitude) * 1000000)
    homeLat = int(float(home_latitude) * 1000000)
    homeLong = int(float(home_longitude) * 1000000)
    return (homeLat -50 < midLat < homeLat +50 and homeLong -50 < midLong < homeLong + 50)
    
    
print("Press ENTER To set lap home")
value = input()
set_home = True
at_home = True
in_lap = False
lap_number = 1
iter = 0
f = open('data.txt', 'w')
starttime = time.ticks_ms()
_thread.start_new_thread(displayTimer, ())
#lock = _thread.allocate_lock()
while True:
    
    if not (lap_number > 1):
        
    
        getGPS(gpsModule)
        
        if(FIX_STATUS == True and set_home == True):
            home_latitude = latitude
            home_longitude = longitude
            print("Home Set At: " + home_latitude + " - " + home_longitude)
            set_home = False
        elif(FIX_STATUS == True and atHome(latitude,longitude) and not in_lap):
            at_home == True
            in_lap == False
            print("Still at home - time not running")
        elif(FIX_STATUS == True and not in_lap):
            print("Lap Started")
            if(at_home == True):
                starttime = time.ticks_ms()
            #lock.acquire()
            at_home == False
            in_lap = True
            #lock.release()
            
        elif(FIX_STATUS == True and in_lap == True):
            iter = iter + 1
            #f.write("WP"+ str(iter) + "," + latitude + "," + longitude + "\n")
            print("Checking lat - " + latitude + " and lon - " + longitude + " against home lat - " + home_latitude + " and home long - " + home_longitude)
            if(atHome(latitude,longitude)):
                in_lap = False
                print("Lap ended, completed lap number - " + str(lap_number))
                lap_number = lap_number + 1
                
        FIX_STATUS = False
        

        
f.close()
