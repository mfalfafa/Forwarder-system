#!/usr/bin/python
import paho.mqtt.client as mqtt
import threading
import sys
import time
import RPi.GPIO as GPIO
from socket import *

print ('*** Data Colector v1.0 ***')
print ('*** miftahf77@gmail.com ***')
print ('*** 24 July 2018 ***')
print ('-----------------------------\n')

# Indicator pin initialization
indicator_pin=25
GPIO.setmode(GPIO.BCM)
GPIO.setup(indicator_pin, GPIO.OUT)
GPIO.output(indicator_pin, 0)

# Start port for clients
serverPort = 5001
# Number of clients
n=15
serverSocket = [socket(AF_INET, SOCK_STREAM)]*n
serverIP = '192.168.10.250'
ready_f=0
while 1:    # Looping until the configurations in server-forwarder is ready   
    try :
        for i in range(n):
            serverSocket[i]=socket(AF_INET, SOCK_STREAM)
            serverSocket[i].setsockopt(SOL_SOCKET, SO_REUSEADDR, 1)
            serverSocket[i].bind((serverIP,serverPort + i))
            serverSocket[i].listen(1)
            #print ('success ' + str(i))
        ready_f=1
    except:
        print ('Your IP Address for socket protocol is incorrect, please setting your IP!')        
        time.sleep(1)
    if ready_f==1:
        break
print ('Number of client : ' + str(n))
connectionSocket=[0]*n
thread=[0]*n

# Socket Server Initialization
lakbanPort = 5000
lakbanSocket = socket(AF_INET, SOCK_STREAM)
lakbanSocket=socket(AF_INET, SOCK_STREAM)
lakbanSocket.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1)
lakbanSocket.bind((serverIP,lakbanPort))
lakbanSocket.listen(1)

# Variables to save data for each client
client=[0]*n

# for sending data ev second
evSecThread=''
buff=[0]*n

# for receiving data from Lakban machine every second
lakbanThread=''
dataLakban=[0]*n

#========= For MQTT ===========
def on_connect(mqttc, obj, flags, rc):
    print("rc: " + str(rc))
    
def on_message(mqttc, obj, msg):
    #print(msg.topic + " " + str(msg.qos) + " " + str(msg.payload))
    msg_buff = msg.topic + " " + str(msg.qos) + " " + str(msg.payload)
    msg_topic = msg.topic
    print (msg_buff)
    
def on_publish(mqttc, obj, mid):
    pass
    #print("publish: " + str(mid))
    
def on_subscribe(mqttc, obj, mid, granted_qos):
    print("Subscribed: " + str(mid) + " " + str(granted_qos))
    
def on_log(mqttc, obj, level, string):
    print(string)

def on_disconnect(client, userdata, rc):
    print ('Problem : '+ str(rc))
    # Trying to reconnect to the server
    ready_f=0
    while 1:
        try:
            mqttc.connect("192.168.10.151", 1883, 60)
            ready_f=1
        except:
            print ('Trying to reconnect to the server...')
        if ready_f==1:
            break

#MQTT Connection
mqttc = mqtt.Client()
mqttc.on_message = on_message
mqttc.on_connect = on_connect
mqttc.on_publish = on_publish
mqttc.on_subscribe = on_subscribe
mqttc.on_disconnect = on_disconnect
# Uncomment to enable debug messages
# mqttc.on_log = on_log
ready_f=0
while 1:    # Looping until the Server is ready   
    try:
        mqttc.connect("192.168.10.151", 1883, 60)
        ready_f=1
    except:
        print ('Waiting for the server...')
        time.sleep(1)
    if ready_f==1:
        break
    
# If All configuration is ready, then set indicator led to on
if ready_f == 1:
    GPIO.output(indicator_pin, 1)
    
def main(argv):
    global client,evSecThread,lakbanThread,dataLakban
    class myThread (threading.Thread):
       def __init__(self, name, serverSocket, port, no):
          threading.Thread.__init__(self)
          self.name = name
          self.serverSocket = serverSocket
          self.port = port
          self.no = no
       def run(self):
          print ('Port : '+ str(self.port)+ ' for '+ self.name + ' is ready.\n')
          sockData(self.name, self.serverSocket, self.port, self.no)
          
    class evSecondThread(threading.Thread):
        def __init__(self):
            threading.Thread.__init__(self)
        def run(self):
            sendData()

    class evSecondLakbanThread(threading.Thread):
        def __init__(self, name, lakbanSocket, port):
            threading.Thread.__init__(self)
            self.name=name
            self.lakbanSocket=lakbanSocket
            self.port=port
        def run(self):
            print ('Port : '+ str(self.port)+ ' for '+ self.name + ' is ready.\n')
            receiveData(self.name, self.lakbanSocket, self.port)

    # For receiving data ecery second from Lakban machine
    def receiveData(name, lakbanSocket, port):
        global dataLakban,n
        try:
            while 1:
                # Accept connection from client (blocking mode)
                connSocket, addr = lakbanSocket.accept()
                #print(connectionSocket.getpeername())
                #print (name + ' , Port : ' + str(port))
            
                # Receives data message from lakban machine
                msg=connSocket.recv(255)
                msg=msg.decode('ascii')
                print (msg)
                # Parsing msg
                # Insert data to variable data lakban
                for i in range(n):
                    dataLakban[i]=1
                connSocket.close()

        except KeyboardInterrupt:
            pass
        except Exception as e:
            print (str(e))

    # Sending data every second
    def sendData():
        global collector,buff,n,client,dataLakban
        while 1:
            time.sleep(1)
            data=''
            # For 4 lines (n-1)
            for i in range(n-1):
                data=data+str(client[i])
            data='{'+data+'}'
            try:
                mqttc.publish("ev_second",data,0)
            except:
                print("There is an error on Sending Data!");

    # Get data from all clients
    def sockData( name, serverSocket, port, no):
        global client,buff
        try:
            while 1:
                # Accept connection from client (blocking mode)
                connectionSocket[no], addr = serverSocket.accept()
                #print(connectionSocket.getpeername())
                #print (name + ' , Port : ' + str(port))
            
                # Receives data message from Socket Client
                msg=connectionSocket[no].recv(1024)
                msg=msg.decode('ascii')
                print (msg)
                # Parsing msg
                # Get data for each client
                client[no]=msg
                # buff[no]=buff[no]+1

                # Sends ACK message to Client
                connectionSocket[no].send('ack'.encode('utf-8'))
                while 1:
                    try:
                        msg=connectionSocket[no].recv(32)
                        msg=msg.decode('ascii')
                    except:
                        print (name + ' is closed!')
                        connectionSocket[no].close()
                        break
                    if msg=='ok':
                        connectionSocket[no].close()
                        break
        except KeyboardInterrupt:
            pass
        except Exception as e:
            print (str(e))

    # Create new threads
    try:
        for i in range(n):
            name="Client-"+str(i)
            thread[i] = myThread(name, serverSocket[i], serverPort+i, i)
    except Exception as e:
            print ("Error: unable to start thread!")
            print (str(e))

    # Create new thread for sending data every second
    try:
        evSecThread=evSecondThread()
    except Exception as e:
        print ("Error: unable to start thread!")
        print (str(e))

    # Create new thread for Lakban machine for every second
    try:
        name="Lakban-0"
        lakbanThread=evSecondLakbanThread(name, lakbanSocket, lakbanPort)
    except Exception as e:
        print ("Error: unable to start thread!")
        print (str(e))

    # Start new Threads
    for i in range(n):
        thread[i].start()
    # Start new thread for sending data ev second and Lakban thread
    evSecThread.start()
    lakbanThread.start()
    
    while 1:
        mqttc.loop(timeout=0.001)
        pass

if __name__=="__main__":
    try:
        main(sys.argv)
    except KeyboardInterrupt:
        pass
    except Exception as e:
        print (str(e))
    finally:
        # Turn off indicator light
        GPIO.output(indicator_pin, 0)
        GPIO.cleanup()

# Note :
# For this data collector script will send data at every second, doesn't matter if all data are received or not.
# Press ALT+F4 to exit this program
