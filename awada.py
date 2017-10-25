#coding:utf-8
import sys
import socket
import time
import multiprocessing
import threading

def usage():
    print('awada portftd')
    print('-h; help')
    print('-listen portA,portB; listen two ports and transmit data')

def subTransmit(recvier,sender,stopflag):
    while not stopflag['flag']:
        try:
            data = recvier[0].recv(20480)
            print("Recv from ",recvier[1])
            sender[0].send(data)
            print("Send to ",sender[1])
        except:
            stopflag['flag'] = True
            try:
                recvier[0].close()
                sender[0].close()
            except:
                pass

def transmit(conns):
    stopFlag = {'flag':False}
    connA, addressA, connB, addressB = conns
    threading.Thread(target=subTransmit,args=((connA,addressA),(connB,addressB), stopFlag)).start()
    threading.Thread(target=subTransmit, args=((connB, addressB), (connA, addressA), stopFlag)).start()
    while not stopFlag['flag']:
        time.sleep(3)
    print("Connection closed.",addressA,addressB)

def bindToBind(portA,portB):
    socketA = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
    socketA.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

    socketB = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    socketB.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

    try:
        print("Listen port %d." % portA)
        socketA.bind(('0.0.0.0',portA))
        socketA.listen()
        print("Listen port ok!")
    except:
        print("Listen port failed!")
        exit()

    try:
        print("Listen port %d." % portB)
        socketB.bind(('0.0.0.0',portB))
        socketB.listen()
        print("Listen port ok!")
    except:
        print("Listen port failed!")
        exit()

    while(True):
        print("Wait for connection at port %d" % portA)
        connA, addressA = socketA.accept()
        print("Accept connection from ",addressA)
        print("Wait for another connection at port %d" % portB)
        connB, addressB = socketB.accept()
        print("Accept connecton from ",addressB)
        multiprocessing.Process(target=transmit,args=((connA,addressA,connB,addressB),)).start()
        time.sleep(1)
        print("Create thread ok!")


def main():
    lenOfArgv = len(sys.argv)
    if lenOfArgv <= 1:
        usage()
        exit()
    elif lenOfArgv == 2 and sys.argv[1] == '-h':
        usage()
        exit()
    elif lenOfArgv == 4:
        if sys.argv[1] == '-listen':
            try:
                portA = int(sys.argv[2])
                portB = int(sys.argv[3])
                assert portA != 0 and portB != 0
                bindToBind(portA,portB)
            except:
                print("Bad parameters")
        else:
            usage()

if __name__ == '__main__':
    main()