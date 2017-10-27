#!/usr/local/bin/python3
#coding:utf-8
import sys
import socket
import time
import multiprocessing
import threading
import select

def usage():
    print('AWADA port forward tools')
    print('-h: help')
    print('-v: verbose')
    print('-listen portA,portB: listen two ports and transmit data')
    print('-tran localport,targetip,targetport: listen a local port and transmit data from localport to target:targetport')
    print('-slave reverseip,reverseport,targetip,targetport: connect reverseip:reverseport with targetip:targetport')

def subTransmit(recvier,sender,stopflag):
    theRecvier = recvier[0]
    theSender = sender[0]
    verbose = False
    i = 0
    recvierData = b""
    senderData = b""
    if '-v' in sys.argv:
        verbose = True
    while not stopflag['flag']:
        data = b""
        try:
            rlist, wlist, elist = select.select([theRecvier,theSender],[theRecvier,theSender],[],0.1)
            if len(rlist) != 0:
                for socketer in rlist:
                    data = socketer.recv(20480)
                    if len(data) == 0:
                        raise Exception('连接已断开')
                    if socketer == theRecvier:
                        senderData += data
                        address = recvier[1]
                    else:
                        recvierData += data
                        address = sender[1]
                    bytes = len(data)
                    if verbose:
                        print("Recv From %s:%d" % address," %d bytes" % bytes)
            if len(senderData) != 0:
                bytes = len(senderData)
                if verbose:
                    print("Send to %s:%d" % sender[1]," %d bytes" % bytes)
                theSender.send(senderData)
                senderData = b""
            if len(recvierData) != 0:
                bytes = len(recvierData)
                if verbose:
                    print("Send to %s:%d", recvier[1], " %d bytes" % bytes)
                theRecvier.send(recvierData)
                recvierData = b""
        except Exception as e:
            stopflag['flag'] = True
            try:
                theRecvier.shutdown(socket.SHUT_RDWR)
                theRecvier.close()
            except:
                pass
            try:
                theSender.shutdown(socket.SHUT_RDWR)
                theSender.close()
            except:
                pass
            print("Closed Two Connections")

def transmit(conns,lock=None):
    stopFlag = {'flag':False}
    connA, addressA, connB, addressB = conns
    threading.Thread(target=subTransmit,args=((connA,addressA),(connB,addressB), stopFlag)).start()
    while not stopFlag['flag']:
        time.sleep(1)
    print("%s:%d" % addressA,"<->","%s:%d" % addressB," Closed")

def bindToBind(portA,portB):
    socketA = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
    socketA.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

    socketB = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    socketB.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

    try:
        print("Listen Port %d." % portA)
        socketA.bind(('0.0.0.0',portA))
        socketA.listen(10)
        print("Listen Port Ok!")
    except:
        print("Listen Port Failed!")
        exit()

    try:
        print("Listen Port %d." % portB)
        socketB.bind(('0.0.0.0',portB))
        socketB.listen(10)
        print("Listen Port Ok!")
    except:
        print("Listen port Failed!")
        exit()

    while(True):
        print("Wait For Connection At Port %d" % portA)
        connA, addressA = socketA.accept()
        print("Accept Connection From %s:%d" % addressA)
        print("Wait For Another Connection At Port %d" % portB)
        connB, addressB = socketB.accept()
        print("Accept Connecton From %s:%d" % addressB)
        multiprocessing.Process(target=transmit,args=((connA,addressA,connB,addressB),)).start()
        time.sleep(1)
        print("Create Thread Ok!")

def bindToConn(port,target,targetPort):
    socketA = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
    socketA.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

    localAddress = ('0.0.0.0',port)
    targetAddress = (target,targetPort)

    try:
        print("Listen Port %d." % port)
        socketA.bind(localAddress)
        socketA.listen(10)
        print("Listen Port Ok!")
    except:
        print("Listen Port Failed!")
        exit()

    while True:
        print("Wait For Connection At Port %d" % localAddress[1])
        connA, addressA = socketA.accept()
        print("Accept Connection From %s:%d" % addressA)
        targetConn = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
        targetConn.settimeout(5)
        try:
            targetConn.connect(targetAddress)
            multiprocessing.Process(target=transmit,args=((connA,addressA,targetConn,targetAddress),)).start()
            time.sleep(1)
            print("Create Thread Ok!")
        except TimeoutError:
            print("Connect To %s:%d Failed!" % targetAddress)
            connA.close()
            exit()
        except:
            print("Something wrong!")
            connA.close()
            exit()

def connToConn(reverseIp,reversePort,targetIp,targetPort):
    reverseAddress = (reverseIp, reversePort)
    targetAddress = (targetIp, targetPort)
    while True:
        data = b""
        reverseSocket = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
        targetSocket = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
        try:
            print("Connect To %s:%d" % reverseAddress)
            reverseSocket.connect(reverseAddress)
            print("Connect Ok!")
        except:
            print("Connect Failed!")
            exit()
        while True:
            try:
                if select.select([reverseSocket],[],[]) == ([reverseSocket],[],[]):
                    data = reverseSocket.recv(20480)
                    if len(data) != 0:
                        break
            except:
                continue

        while True:
            try:
                print("Connect ot ",targetAddress)
                targetSocket.connect(targetAddress)
                print("Connect ok!")
            except:
                print("TargetPort Is Not Open")
                reverseSocket.close()
                exit()
            try:
                targetSocket.send(data)
            except:
                continue
            break
        print("All Connect Ok!")

        try:
            multiprocessing.Process(target=transmit,args=((reverseSocket,reverseAddress,targetSocket,targetAddress),)).start()
            print("Create Thread Success!")
            #time.sleep(1)
        except:
            print("Create Thread Failed!")
            exit()

def main():
    global verbose
    if '-h' in sys.argv:
        usage()
        exit()
    if '-listen' in sys.argv:
        index = sys.argv.index('-listen')
        try:
            portA = int(sys.argv[index+1])
            portB = int(sys.argv[index+2])
            assert portA != 0 and portB != 0
            bindToBind(portA,portB)
        except:
            print("Something Wrong")
        exit()

    elif '-tran' in sys.argv:
        index = sys.argv.index('-tran')
        try:
            port = int(sys.argv[index+1])
            target = sys.argv[index+2]
            targetPort = int(sys.argv[index+3])
            assert port!=0 and targetPort!=0
            bindToConn(port,target,targetPort)
        except:
            print("Something Wrong")
        exit()
    elif '-slave' in sys.argv:
        index = sys.argv.index('-slave')
        try:
            reverseIp = sys.argv[index+1]
            reversePort = int(sys.argv[index+2])
            targetIp = sys.argv[index+3]
            targetPort = int(sys.argv[index+4])
            connToConn(reverseIp,reversePort,targetIp,targetPort)
        except:
            print("Something Wrong")
        exit()
    usage()

if __name__ == '__main__':
    main()
