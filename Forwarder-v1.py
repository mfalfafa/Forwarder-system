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
reject = 'Y8'
good = 'DT972'

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
                #Get command header from HMI
                cmd_header=cmd_from_hmi[0:len('%01#RDD')]
                # Execution for Read data register
                if cmd_header == '%01#RDD':  
                    #Parsing CMD from HMI and get all addresses
                    cmd_from_hmi_with_bcc=cmd_from_hmi[len(cmd_len_rd):]
                    addrs=cmd_from_hmi_with_bcc[0:len(cmd_from_hmi_with_bcc)-3]
                    # Get start and end address
                    start_addr=addrs[0:5]
                    end_addr=addrs[5:]
                    n=int(end_addr)-int(start_addr)
                    addrs=[]
                    for i in range(n+1):
                        addrs.append(int(start_addr)+i)
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
                            if cmd_header == '%01#RDD':
                                #Parsing data register from PLC
                                dt_with_bcc=resp[len(resp_len):]
                                l=len(dt_with_bcc)
                                dt=dt_with_bcc[0:l-3]   #3 means BCC + RC length

                                #Get data each register if there are more than 1 register
                                n=0
                                l=len(dt)/4     #4 = word register in Hex (HHHH)
                                vals=[]
                                for j in range(l):
                                    vals.append(dt[n:n+4])
                                    #Swap the value of 1 register
                                    l=len(vals[j])/2
                                    dt_sw=vals[j][l:]+vals[j][0:l]
                                    dt_dec=int(dt_sw, 16)
                                    vals[j]=dt_dec
                                    n=n+4

                            #Send data to HMI
                            ser_to_hmi.write(resp)

                            if cmd_header == '%01#RDD':
                                #Send to PC Server (Addresses and Values)
                                all_data=[addrs,vals]
                                all_data=str(all_data)
                                # Client Socket Connection
                                # Using Socket Connection to send all data from PLC to PC Server
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
                                    # ++++++
                                    for i in range(sensorNo):
                                        # Add Sensor 1 to 14 here, sensor numb. 15 in Server Forwarder. Parsing data from PLC here !
                                        sen[i]='"s'+str(i+1)+'":'+str(random.randint(1,21))
                                    sen_data=''
                                    for i in range(sensorNo):
                                        sen_data=sen_data+sen[i]+','
                                    all_data='"'+'line'+str(line)+'":{"line":'+str(line)+','+sen_data+'"ts":'+str(time.time())+'},'
                                    print (all_data)
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

    
        


