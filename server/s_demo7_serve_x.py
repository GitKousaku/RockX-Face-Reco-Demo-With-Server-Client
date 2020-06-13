#coding:Shift-JIS
import face_reco4x0 as face_reco
import pyscreenshot as ImageGrab
import numpy as np
import cv2
import tkinter
import PIL.Image,PIL.ImageTk
import sys
import os
#from PyQt5.QtWidgets import (QWidget, QLabel, QLineEdit, 
#                             QTextEdit, QGridLayout, QApplication, QPushButton,  QDesktopWidget)
#from PyQt5.QtGui import QIcon
#from PyQt5.QtCore import QUrl
from PyQt5.QtWebEngineWidgets import QWebEngineView
from PyQt5.QtCore import *
from PyQt5.QtWidgets import *
from PyQt5.QtGui import *
from PyQt5 import QtCore
import argparse
from pygame import mixer
import subprocess
import time
import socket

HEADER_SIZE=4
NAME_SIZE=20
IMAGE_QUALITY=30
PACKET_CLIENT_SIZE=30
REGISTRATION_MODE=1
EVALUATION_MODE=0
ERASE_MODE=2
UPDATE_FPS=10



class MainWindow(QMainWindow):
    #repeatTime=500 #ms
    v_width=640
    v_height=480

    def __init__(self,parent=None):
        super(MainWindow,self).__init__(parent)
        
        self.repeatTime =args.itimer #ms Update Time
        self.count=1
        
        self.cap=cv2.VideoCapture(int(args.camera))
        print
        if self.cap.isOpened() is False:
            raise("IO Error")
        self.view = QGraphicsView()
        self.view2 = QGraphicsView()

        size = (self.v_width, self.v_height)
        self.cap.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc('M', 'J', 'P', 'G')) # need otherwise select YUV and become slow
        self.cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH ,self.v_width)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT,self.v_height)
        self.setGeometry(0, 0, 840, 400)
        self.setWindowTitle('RockX Face Recog')
        
        #window setup
        self.widget = QWidget()
        self.view = QGraphicsView()

        self.scene = QGraphicsScene()
        self.scene2 = QGraphicsScene()
        self.stat=0
        

        self.view.setMouseTracking(True)
        self.view.viewport().installEventFilter(self)
        self.view.setScene(self.scene)
        #ぴったり合わせるおまじない
        #self.view.fitInView(self.scene.sceneRect(), Qt.KeepAspectRatio)
        #レイアウトの作成
        self.main = QGridLayout()
        #label & buttonの表示
        self.label = QLabel("RegistrationName")
        self.entry = QLineEdit()
        self.regist = QPushButton('RegistrationMode')
        self.reg_ok = QPushButton('Registration')
        self.eval   = QPushButton("EvaluateMode")
        self.result = QLineEdit()
        self.erase   = QPushButton("Erase FaceDB")
        self.auto=QCheckBox('auto Detection')
        self.auto.toggle()


        #signalの設定
        if args.full == 1:
       	    self.main.addWidget(self.eval,          0,1,1,1)
            self.main.addWidget(self.regist,        1,1,1,1)
            self.main.addWidget(self.auto,          2,1,1,1)
            self.main.addWidget(self.label,         3,1,1,1)
            self.main.addWidget(self.entry,         4,1,1,1)
            self.main.addWidget(self.reg_ok,        5,1,1,1)
            self.main.addWidget(self.erase,         6,1,1,1)
            self.main.addWidget(self.result,        7,1,1,1)
            self.main.addWidget(self.view2,         8,1,1,1)
            self.main.addWidget(self.view,          0,0,20,1)
        else:
       	    #self.main.addWidget(self.eval,          0,1,1,1)
            #self.main.addWidget(self.regist,        1,1,1,1)
            #self.main.addWidget(self.auto,          2,1,1,1)
            self.main.addWidget(self.label,         3,1,1,1)
            self.main.addWidget(self.entry,         4,1,1,1)
            self.main.addWidget(self.reg_ok,        5,1,1,1)
            self.main.addWidget(self.erase,         6,1,1,1)
            self.main.addWidget(self.result,        7,1,1,1)
            self.main.addWidget(self.view2,         8,1,1,1)
            #self.main.addWidget(self.view,          0,0,20,1)
            self.setGeometry(0, 0, 200, 120)

        self.widget.setLayout(self.main)
        self.setCentralWidget(self.widget)

        self.regist.clicked.connect(self.buttonRegMode)
        self.reg_ok.clicked.connect(self.buttonOK)
        self.eval.clicked.connect(self.EvalMode)
        self.erase.clicked.connect(self.EraseFaceDB)
        self.auto.clicked.connect(self.AutoReg)

        self.mode=0
        self.reg_on=0
        self.x0=0
        self.x1=0
        self.y0=0
        self.y1=0
        self.faceinit=0
        self.face_db_erase =0
        self.reg_auto=True
        self.face_detected=False
        self.reg_name="default"

        self.mes='                   '
        self.face_db,reco_keys=face_reco.rock_init()

        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.setsockopt(socket.SOL_SOCKET,socket.SO_REUSEADDR,1)
        #s.bind(('192.168.2.115', 50007))
        s.bind((args.ip, 50007))
        s.listen(1)
        self.soc, self.addr = s.accept()
        #print("Recv Address",self.addr)

        self.set()


        #update timer
        timer = QTimer(self.view)
        timer.timeout.connect(self.set)
        timer.start(self.repeatTime)

    def buttonRegMode(self):
        self.mode=1
        
        print("Registration Mode")

    def buttonOK(self):
        self.reg_on=1
        fname=self.entry.text()
        print("Registration Done to ",fname)

    def EvalMode(self):
        self.mode=EVALUATION_MODE

    def AutoReg(self):
        self.reg_auto= not self.reg_auto
        print("AutoRegFlag ",self.reg_auto)

    def EraseFaceDB(self):
        self.mode=ERASE_MODE

    def eventFilter(self, source, event):
        offset=40
        if event.type() == QtCore.QEvent.MouseMove:
            if event.buttons() == QtCore.Qt.NoButton:
                pass
                #print("Simple mouse motion",event.x(),event.y())
            elif event.buttons() == QtCore.Qt.LeftButton:
                #print("Left click drag",event.x(),event.y())
                self.x1=event.x()-offset
                self.y1=event.y()
            elif event.buttons() == QtCore.Qt.RightButton:
                pass
                #print("Right click drag",event.x(),event.y())
        elif event.type() == QtCore.QEvent.MouseButtonPress:
            if event.button() == QtCore.Qt.LeftButton:
                #print("Press!",event.x(),event.y())
                self.x0=event.x()-offset
                self.x1=self.x0
                self.y0=event.y()
                self.y1=self.y0
        return super(MainWindow, self).eventFilter(source, event)

    def set(self):  # Update Function
        #self.repeatTime=20
        #self.repeatTime=args.itimer
        #print("Count ",self.count)
        self.count=self.count+1
        #UpdateTiming
        loop_start_time = time.time()
        
        self.mes="NoSense:".ljust(NAME_SIZE)
        self.stat=0
        
        #camera capture
        ret_cap,frame=self.cap.read()
        
        if ret_cap == False:
           print("FFAFAF")
           self.cap.release()
           #self.soc.shutdown(socket.SHUT_RDWR)
           self.soc.close()
           exit()

        frame = cv2.cvtColor(frame,cv2.COLOR_BGR2RGB)

        #face detection
        if ret_cap:
           ret_reco,names,boxes,scores=face_reco.rock(frame)
           if ret_reco == -1:
              face_reco.rock_init()
           if len(boxes)>0:
              self.face_detected=True
              self.stat=1
           else:
              self.face_detected=False
              self.stat=0

        if len(boxes) > 0:
            bl=boxes[0].left
            bt=boxes[0].top
            br=boxes[0].right
            bb=boxes[0].bottom
            ml=bl-60
            mt=bt-60
            mr=br+60
            mb=bb+60
            #cv2.rectangle(frame,(boxes[0].left,boxes[0].top),(boxes[0].right,boxes[0].bottom),(0,255,0),thickness=1)
            if self.reg_auto and self.mode != REGISTRATION_MODE:
                cv2.rectangle(frame,(ml,mt),(mr,mb),(255,0,0),thickness=1)
        
        regstration_OK=False

        if  ret_cap and self.mode == REGISTRATION_MODE and not self.reg_auto: # registration
            cv2.rectangle(frame,(boxes[0].left,boxes[0].top),(boxes[0].right,boxes[0].bottom),(0,255,0),thickness=1)
            cv2.rectangle(frame,(self.x0,self.y0),(self.x1,self.y1),(0,0,255),thickness=2)
            if self.reg_on == 1:
                cut_frame=frame[self.y0:self.y1,self.x0:self.x1] #Slice y0->y1  x0->x1
                fname=self.entry.text()
                self.y0=0
                self.y1=0
                self.x0=0
                self.x1=0
                regstration_OK=True

        if  self.reg_on == 1:
            if self.reg_auto:
                if self.face_detected==True:
                   mt=max(0,mt)
                   ml=max(0,ml)
                   mr=min(frame.shape[1],mr)
                   mb=min(frame.shape[0],mb)
                   cut_frame=frame[mt:mb,ml:mr] ### Slice
                   fname=self.reg_name
                   regstration_OK=True

        if self.reg_on == 1:
            if regstration_OK:
                cv2.imwrite("./image/"+fname+".jpg",cut_frame)
                face_reco.import_face(self.face_db)
                print("import Face DB :",self.face_db)
                regstration_OK=False
                self.reg_on=0
                self.entry.setText('')
                self.mode=EVALUATION_MODE
            else:
                print("Cant Regist")

        if  self.mode==ERASE_MODE:
            self.repeatTime=100
            subprocess.run(['sh', 'removeFace.sh'])
            face_reco.import_face(self.face_db)
            self.mode=REGISTRATION_MODE
            self.repeatTime=args.itimer
        
        if ret_cap and self.mode == EVALUATION_MODE:  #evaluation
            msg=None
            for box,name,score in zip(boxes,names,scores):
                cv2.rectangle(frame,(box.left,box.top),(box.right,box.bottom),(0,255,0),thickness=1)
                if name is not None:
                   msg=name+"("+str(round(score,2))+")"
                   self.result.setText(msg)
                   #self.mes="{:20}".format("Recog:"+name+"("+str(round(score,2))+")")[:NAME_SIZE]
                   self.mes=("Recog:"+name+"("+str(round(score,2))+")").ljust(NAME_SIZE)
                   self.mes=self.mes[:NAME_SIZE] #NEED TO CUT
                   #print("Recog",self.mes,len(self.mes))
                   #cv2.rectangle(frame,(box.left,box.top),(box.right,box.bottom),(0,255,0),thickness=1)
                   self.stat=2
                   if name == args.t_name:
                      if args.sound == 1 :
                         mixer.music.play(1)
                else:
                   msg="No Recognize"
                   self.result.setText(msg)
                   #self.mes="{:20}".format("NoReco:")[:NAME_SIZE]
                   self.mes=("NoReco:").ljust(NAME_SIZE)
                   self.stat=1
            self.result.setText(msg)
        if ret_cap == 1:
	        #Send Packet Creattion
	        send_img=cv2.resize(frame,(640,480))#
	        (status, encoded_img) = cv2.imencode('.jpg', send_img, [int(cv2.IMWRITE_JPEG_QUALITY), IMAGE_QUALITY])
	        packet_body = encoded_img.tostring()
	        #packet_name = 'TakiguchiT'.encode()
	        #print("SendMes:",self.mes,len(self.mes))
	        packet_name = self.mes.encode()
	        packet_header = len(packet_body).to_bytes(HEADER_SIZE, 'big') 
	        packet = packet_header + packet_name+packet_body
	        #packet = packet_header + packet_body
	        #print("PAK",len(packet_body),packet_header)
	        try:
                    self.soc.sendall(packet)
	        except:
                    self.cap.release()
                    #self.soc.shutdown(socket.SHUT_RDWR)
                    self.soc.close()
                    exit()
	        #Receive Packet
	        rcv_data=self.soc.recv(PACKET_CLIENT_SIZE)
	        rcv_data=rcv_data.decode()
	        #print("rcv",rcv_data,len(rcv_data))
	        # com anal
	        command=rcv_data[0:rcv_data.find(":")]
	        content=rcv_data[rcv_data.find(":")+1:]
	        if command == "reg_name":
	            self.entry.setText(content)
	            self.reg_name=content
	            print("---",self.entry)          
	 
	        #Window Update
	        height, width, dim = frame.shape
	        bytesPerLine = dim * width
	        self.image = QImage(frame.data, width, height, bytesPerLine, QImage.Format_RGB888)
	        self.item = QGraphicsPixmapItem(QPixmap.fromImage(self.image))
	        self.scene.addItem(self.item)
	        self.view.setScene(self.scene)
	        
	        img2=cv2.imread("r.jpg")
	        if self.stat == 2:
	           img2=cv2.imread("g.jpg")
	        if self.stat == 1:
	           img2=cv2.imread("y.jpg")
	        img2=cv2.cvtColor(img2,cv2.COLOR_BGR2RGB)

	        height, width, dim = img2.shape
	        bytesPerLine = dim * width
	        self.image2 = QImage(img2.data, width, height, bytesPerLine, QImage.Format_RGB888)
	        self.item2 = QGraphicsPixmapItem(QPixmap.fromImage(self.image2))
	        self.scene2.addItem(self.item2)
	        self.view2.setScene(self.scene2)

        #Update Time Adjustment 
        #print("Seelp",max(0, 1 / UPDATE_FPS - (time.time() - loop_start_time)))
        time.sleep(max(0, 1 / UPDATE_FPS - (time.time() - loop_start_time)))
    def __del__(self):
        print("Destractor")
        self.cap.release()
        #self.soc.shutdown(socket.SHUT_RDWR)
        self.soc.close()

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="RockX Face Recognition Demo")
    parser.add_argument('-s','--sound',help="sound",type=int,default=0)
    parser.add_argument('-n','--t_name',help='target name',type=str,default='taki')
    parser.add_argument('-a','--apmode',help='wifi ap mode',type=int,default=0)
    parser.add_argument('-w','--wifi',help='wifi cam',type=int,default=1)
    parser.add_argument('-t','--itimer',help='interval time',type=int,default=10)
    #parser.add_argument('-i','--ip',help='interval time',default="172.20.10.2")
    parser.add_argument('-i','--ip',help='interval time',default="192.168.2.118")
    parser.add_argument('-c','--camera',help='camera id',type=int,default=0)
    parser.add_argument('-f','--full',help='full scale',type=int,default=0)
    args=parser.parse_args()
    print(args.camera)
    mixer.init()
    mixer.music.load("button06.mp3")


    app = QApplication(sys.argv)
    main_window = MainWindow()
    main_window.show()
    app.exec_()

