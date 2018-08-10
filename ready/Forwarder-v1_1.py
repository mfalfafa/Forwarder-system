# Forwarder v1.0
# Program for reading data from specific address in FPSigma Panasonic PLC v1.0
# using MEWTOCOL-COM Protocol RS232
# Created by MF ALFAFA
# 8 July 2018
# miftahf77@gmail.com

# How to use :
# Change the "serverIP and serverPort according to PC Socket Server"
# Connect Kinco HMI and FPSigma Panasonic to USB0 and USB1 in Raspi 3
# Run this program, and all data from PLC will flow to PC Server

import serial
import time
import threading
import RPi.GPIO as GPIO
from socket import *

print ('Client 1')

## Client Socket Communication initialization
serverIP = '192.168.10.250'    # PC Server IP
serverPort = 5001               # PC Server Port
clientSocket=''

## Variables for serial data response
connected = False
ser_to_hmi = 0
ser_to_plc = 0
x=0
y=0
cmd_from_hmi=''
resp=''

## FPSigma commands initialization
resp_len='%01$RD'                           #same length as %01$RC
resp_len_RC='%01$RC'
cmd_len_rd='%01#RDD'
cmd_len_rc='%01#RCSR'
addrs=[]
vals=[]

# Addresses for FPSigma
# -Reject = y8, r113
# -Good = DT972, r112
data_reject = ''
data_good = ''
total_reject=0
total_production=0
data_reject_ready=0
data_good_ready=0

#Flag for error
e_f=0
conn_f=0

# Indicator pin initialization
indicator_pin=25
GPIO.setmode(GPIO.BCM)
GPIO.setup(indicator_pin, GPIO.OUT)
GPIO.output(indicator_pin, 0)

## Establish connection to COM Port
## Connection from HMI
locations=['/dev/ttyUSB0']
## loop until the device tells us it is ready
while not connected:
    ## COM Port settings
    for device in locations: 
        try:
            # print ("Trying...",device)
            ## Serial Initialization
            ser_to_hmi = serial.Serial(device,      #port
                                19200,              #baudrate
                                serial.EIGHTBITS,   #bytesize
                                serial.PARITY_ODD,  #parity
                                serial.STOPBITS_ONE,#stop bit
                                0,                  #timeout
                                False,              #xonxoff
                                False,              #rtscts
                                0,                  #write_timeout
                                False,              #dsrdtr
                                None,               #inter byte timeout
                                None                #exclusive
                                )
            connected=True
        except:
            connected=False
            print ("trying to connect to ", device)
            time.sleep(1.5)
if connected:
    serin = ser_to_hmi.read()
    print ("Connected to ",device)
    connected=False

## Try to connect to PLC
device = '/dev/ttyUSB1'
## loop until the device tells us it is ready
while not connected:
    try:
        # print ("Trying...",device)
        ## Serial Initialization
        ser_to_plc = serial.Serial(device,      #port
                            19200,              #baudrate
                            serial.EIGHTBITS,   #bytesize
                            serial.PARITY_ODD,  #parity
                            serial.STOPBITS_ONE,#stop bit
                            0,                  #timeout
                            False,              #xonxoff
                            False,              #rtscts
                            0,                  #write_timeout
                            False,              #dsrdtr
                            None,               #inter byte timeout
                            None                #exclusive
                            )
        connected=True
    except:
        connected=False
        print ("trying to connect to ", device)
        time.sleep(1.5)
if connected:
    serin = ser_to_plc.read()
    print ("Connected to ",device)

class evSecondThread(threading.Thread):
    def __init__(self):
        threading.Thread.__init__(self)
    def run(self):
        sendData()

def sendData():
    global data_reject_ready,data_good_ready,total_production,e_f,clientSocket,conn_f
    while 1:
        if not((data_good_ready == '') and (data_reject_ready =='')):
            print ('data to forwarder server')
            while 1:
                try:
                    clientSocket=socket(AF_INET, SOCK_STREAM)
                    clientSocket.connect((serverIP, serverPort))
                    conn_f=1
                    break
                except Exception as e:
                    e_f=1
                    print ('error : '+ str(e))
                    break #+++
            if e_f==1:
                e_f=0
                if conn_f==1:
                    clientSocket.close()
                    conn_f=0
            else:
                conn_f=1
                # Send all data (Total production and Data Good)
                all_data = '@'+str(total_production) +'@'+ str(data_good_ready)+'@'
                clientSocket.send(all_data.encode('utf-8'))
                while 1:
                    try:
                        msg=clientSocket.recv(32)
                        msg=msg.decode('ascii')
                        # Get 'ack' from Socket Server
                        if msg=='ack':
                            clientSocket.send('ok'.encode('utf-8'))
                            clientSocket.close()
                            break
                        elif msg=='closed':
                            print ('Socket Server is closed')
                            clientSocket.close()
                            break
                    except Exception as e:
                        print (str(e))
                        #clientSocket.close()
                        break
        time.sleep(0.5)

# Create new thread for sending data every second
try:
    evSecThread=evSecondThread()
except Exception as e:
    print ("Error: unable to start thread!")
    print (str(e))
# Start thread
evSecThread.start()

# If ready then turn on indicator light
GPIO.output(indicator_pin, 1)
while 1:
    try:
        # Waiting data from HMI
        if ser_to_hmi.inWaiting():
            x=ser_to_hmi.read()
            x=x.decode('ascii')
            cmd_from_hmi=cmd_from_hmi + x
            if x == '\r':
                # print ("data from HMI :")
                #print (cmd_from_hmi)

                #Send CMD to PLC to get response
                ser_to_plc.write(cmd_from_hmi.encode('utf-8'))
                #waiting for incoming serial data from PLC
                h=0
                while 1 :
                    h=h+1
                    # Timeout delay if there is no response from PLC
                    if h>=1000000:  
                        break
                    if ser_to_plc.inWaiting():
                        y=ser_to_plc.read()
                        y=y.decode('ascii')
                        resp=resp + y
                        if y=='\r':
                            # print ("data from plc :")
                            #print (resp)

                            #Send data to HMI
                            ser_to_hmi.write(resp.encode('utf-8'))

                            # Get reject value
                            reject_cmd = '%01#RCSY0008**\r'
                            ser_to_plc.write(reject_cmd.encode('utf-8'))
                            data_reject=''
                            data_reject_ready=''
                            # Waiting data from PLC
                            h=0
                            while 1:    
                                h=h+1
                                # Timeout delay
                                if h>=1000000:
                                    break
                                if ser_to_plc.inWaiting():
                                    y=ser_to_plc.read()
                                    y=y.decode('ascii')
                                    data_reject=data_reject + y
                                    if y=='\r':
                                        print (data_reject)
                                        # Parsing data
                                        dt_with_bcc=data_reject[len(resp_len_RC):]
                                        l=len(dt_with_bcc)
                                        dt=dt_with_bcc[0:l-3]   #3 means BCC + RC length
                                        data_reject=int(dt)
                                        data_reject_ready=data_reject
                                        break
                            # Calculate total reject
                            total_reject=total_reject+data_reject_ready

                            # Get good value
                            good_cmd = '%01#RDD0097200972**\r'
                            ser_to_plc.write(good_cmd.encode('utf-8'))
                            data_good=''
                            data_good_ready=''
                            # Waiting data from PLC
                            h=0
                            while 1:    
                                h=h+1
                                if h>=1000000: # Timeout delay
                                    break
                                if ser_to_plc.inWaiting():
                                    y=ser_to_plc.read()
                                    y=y.decode('ascii')
                                    data_good=data_good + y
                                    if y=='\r':
                                        print (data_good)
                                        # Parsing data
                                        dt_with_bcc=data_good[len(resp_len):]
                                        l=len(dt_with_bcc)
                                        dt=dt_with_bcc[0:l-3]   #3 means BCC + RC length
                                        data_good=int(dt)
                                        data_good_ready=data_good
                                        break
                            # Get total production
                            total_production=data_good_ready+total_reject
                            resp=''
                            break
                cmd_from_hmi=''
                print ('-----------------')
    except KeyboardInterrupt:
        break
    except Exception as e:
        print ('Error : '+ str(e))
        break

## close the serial connection and text file
print ("Connection is closed!")
ser_to_hmi.close()
ser_to_plc.close()
## close the socket connection
try:
    clientSocket.close()
except:
    print ('clientSocket variable is not initialized!')
    
# Turn off indicator light
GPIO.output(indicator_pin, 0)
GPIO.cleanup()

    
        


