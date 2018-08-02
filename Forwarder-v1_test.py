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
import random
from socket import *

## Client Socket Communication initialization
serverIP = '192.168.10.250'    # PC Server IP
serverPort = 5001               # PC Server Port
# line settings ++++++++
sensorNo=15
sen=[0]*15
line=1

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
cmd_len_rd='%01#RDD'
cmd_len_rc='%01#RCSR'
addrs=[]
vals=[]

# Addresses for FPSigma
# -Reject = y8, r113
# -Good = DT972, r112
data_reject = ''
data_good = ''

## Establish connection to COM Port
## Connection from HMI
locations=['/dev/ttyUSB0']
## COM Port settings
for device in locations: 
    try:
        print ("Trying...",device)
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
        break
    except:
        print ("Failed to connect on ", device)

## loop until the device tells us it is ready
while not connected:
    serin = ser_to_hmi.read()
    connected = True
print ("Connected to ",device)
connected=False

## Try to connect to PLC
device = '/dev/ttyUSB1'
try:
    print ("Trying...",device)
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
except:
    print ("Failed to connect on ", device)
## loop until the device tells us it is ready
while not connected:
    serin = ser_to_plc.read()
    connected = True
print ("Connected to ",device)

e_f=0   #Flag for error +++
while 1:
    try:
        # Waiting data from HMI
        if ser_to_hmi.inWaiting():
            x=ser_to_hmi.read()
            cmd_from_hmi=cmd_from_hmi + x
            if x == '\r':
                # print ("data from HMI :")
                print (cmd_from_hmi)

                #Send CMD to PLC to get response
                ser_to_plc.write(cmd_from_hmi)
                #waiting for incoming serial data from PLC
                while 1 :
                    if ser_to_plc.inWaiting():
                        y=ser_to_plc.read()
                        resp=resp + y
                        if y=='\r':
                            # print ("data from plc :")
                            print (resp)

                            #Send data to HMI
                            ser_to_hmi.write(resp)

                            # Get reject value
                            reject_cmd = '%01#RCSY0008**'
                            ser_to_plc.write(reject_cmd)
                            data_reject=''
                            # Waiting data from PLC
                            while 1:    
                                if ser_to_plc.inWaiting():
                                    y=ser_to_plc.read()
                                    data_reject=data_reject + y
                                    if y=='\r':
                                        print (data_reject)
                                        break
                            # Get good value
                            good_cmd = '%01#RDD0097200972**'
                            ser_to_plc.write(good_cmd)
                            data_good=''
                            # Waiting data from PLC
                            while 1:    
                                if ser_to_plc.inWaiting():
                                    y=ser_to_plc.read()
                                    data_good=data_good + y
                                    if y=='\r':
                                        print (data_good)
                                        break

                            if not((data_good == '') && (data_reject =='')):
                                while 1:
                                    try:
                                        clientSocket=socket(AF_INET, SOCK_STREAM)
                                        clientSocket.connect((serverIP, serverPort))
                                        break
                                    except Exception as e:
                                        e_f=1
                                        print ('error : '+ str(e))
                                        break #+++
                                if e_f==1:
                                    e_f=0
                                else:
                                    all_data = str(data_reject) +'&'+ str(data_good)
                                    clientSocket.send(all_data.encode('utf-8'))
                                    while 1:
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
clientSocket.close()

    
        


