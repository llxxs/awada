#coding:utf-8
import sys
import socket
import time
import multiprocessing
import threading
import select

def usage():
    print('awada portftd')
    print('-h; help')
    print('-listen portA,portB; listen two ports and transmit data')
    print('-tran localport,target,targetport; listen a local port and transmit data to target:targetport')

def subTransmit(recvier,sender,stopflag):
    while not stopflag['flag']:
        data = b""
        try:
            if select.select([recvier[0]],[],[]) == ([recvier[0]],[],[]):
                data = recvier[0].recv(20480)
                if len(data) == 0:
                    time.sleep(0.1) #select加sleep为了多平台都可用
                    continue
            print("Recv from ",recvier[1])
            sender[0].send(data)
            print("Send to ",sender[1])
        except Exception as e:
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
        socketA.listen(10)
        print("Listen port ok!")
    except:
        print("Listen port failed!")
        exit()

    try:
        print("Listen port %d." % portB)
        socketB.bind(('0.0.0.0',portB))
        socketB.listen(10)
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

def bindToConn(port,target,targetPort):
    socketA = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
    socketA.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

    localAddress = ('0.0.0.0',port)
    targetAddress = (target,targetPort)

    try:
        print("Listen port %d." % port)
        socketA.bind(localAddress)
        socketA.listen(10)
        print("Listen port ok!")
    except:
        print("Listen port failed!")
        exit()

    while True:
        print("Wait for connection at port %d" % localAddress[1])
        connA, addressA = socketA.accept()
        print("Accept connection from ",addressA)
        targetConn = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
        targetConn.settimeout(5)
        try:
            targetConn.connect(targetAddress)
            multiprocessing.Process(target=transmit,args=((connA,addressA,targetConn,targetAddress),)).start()
            time.sleep(1)
            print("Create thread ok!")
        except TimeoutError:
            print("Connect to ",targetAddress," failed!")
            connA.close()
            exit()
        except:
            print("Something wrong!")
            connA.close()
            exit()

def main():
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
            print("Something wrong")
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
            print("Something wrong")
        exit()

    usage()

if __name__ == '__main__':
    main()