#coding:Shift_JIS
from kivy.config import Config
Config.set('graphics','resizable',0)

from kivy.core.window import Window
Window.size = (600, 500)


import cv2
import numpy as np
from kivy.app import App
from kivy.lang import Builder
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.clock import Clock
import socket
from threading import *
from kivy.uix.image import Image
from kivy.cache import Cache
import pygame
from kivy.uix.popup import Popup
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from kivy.uix.button import Button
from kivy.properties import StringProperty, ObjectProperty
from kivy.graphics.texture import Texture
import argparse
import configparser

parser = argparse.ArgumentParser(description="RockX Face Recognition Demo")
parser.add_argument('-i','--ip',help='interval time',default="192.168.2.115")
args=parser.parse_args()
config = configparser.ConfigParser()
config.read('./demo_connection.ini', 'Shift_JIS')
config_server_ip = config.get('server', 'ip')
print(config_server_ip)


kv = '''
main:
	label: text_label
	BoxLayout:
		orientation: 'vertical'
		padding: root.width * 0.05, root.height * .05
		spacing: '5dp'
		BoxLayout:
			size_hint: [1,0.8]
			Image:
				id: image_source
				source: 'foo.png'
		BoxLayout:
			size_hint: [1,0.2]
			GridLayout:
				cols: 4
				spacing: '10dp'
				Button:
					id: status
					text:'Play'
					bold: True
					on_press: root.playPause()
				Button:
					text: 'ID Setting'
					bold: True
					on_press: root.setting()
				Button:
					text: 'Registration'
					bold: True
					on_press: root.registration()
				Button:
					text: 'IP Setting'
					bold: True
					on_press: root.settingIP()
		BoxLayout:
			size_hint:[1,0.1]
			GridLayout:
				cols:1
				Label:
					id:text_label
					text:""
					

'''
class main(BoxLayout):
	# 通信用設定
	ipAddress = None
	port = None
	#ipAddress = '172.20.10.2'
	#ipAddress = '192.168.2.115'
	ipAddress = config_server_ip
	port = 50007
	buff = bytes()
	
	#cap = cv2.VideoCapture(0)

	image_texture = ObjectProperty(None)
	label = ObjectProperty(None)
	PACKET_HEADER_SIZE = 4
	PACKET_NAME_SIZE=20  
	IMAGE_HEIGHT=320
	IMAGE_WIDTH=240 
	VIEW_HEIGHT=320
	VIEW_WIDTH=480
	PACKET_CLIENT_SIZE=30
	reg_name=''
	sendflag_regname=False
	sendflag_registration=False

	def playPause(self):
		if self.ids.status.text == "Close":
			self.soc.shutdown(socket.SHUT_RDWR)
			self.soc.close()
			self.close()
		else:
			print("socket create")
			self.soc=socket.socket(socket.AF_INET, socket.SOCK_STREAM)
			print("connect")
			self.soc.connect((self.ipAddress, self.port))
			print("connect done")
			self.ids.status.text = "Close"
			Clock.schedule_interval(self.recv, 0.1)

	def recv(self, dt):
		# サーバからのデータをバッファに蓄積
		
		#print("Receive")
		data = self.soc.recv(self.IMAGE_HEIGHT * self.IMAGE_WIDTH * 3)
		self.buff += data
		
		# 最新のパケットの先頭までシーク
		# バッファに溜まってるパケット全ての情報を取得
		packet_head = 0
		packets_info = list()
		while True:
			#print("Head",packet_head)
			if len(self.buff) >= packet_head + self.PACKET_HEADER_SIZE+self.PACKET_NAME_SIZE:
				binary_size = int.from_bytes(self.buff[packet_head:packet_head + self.PACKET_HEADER_SIZE], 'big')
				#print("------bin",self.buff)
				name=self.buff[packet_head+ self.PACKET_HEADER_SIZE:packet_head + self.PACKET_HEADER_SIZE+self.PACKET_NAME_SIZE]
				#print("------dec_name",name,packet_head+ self.PACKET_HEADER_SIZE,packet_head + self.PACKET_HEADER_SIZE+self.PACKET_NAME_SIZE)
				dec_name=name.decode()
				#dec_name=dec_name[6:dec_name.find("(")]
				self.label.text = dec_name
				print(dec_name)
				if len(self.buff) >= packet_head + self.PACKET_HEADER_SIZE + binary_size+self.PACKET_NAME_SIZE:
					packets_info.append((packet_head, binary_size))
					packet_head += self.PACKET_HEADER_SIZE + binary_size+self.PACKET_NAME_SIZE #
				else:
					break
			else:
				break
		
		# バッファの中に完成したパケットがあれば、画像を更新
		if len(packets_info) > 0:

			# 最新の完成したパケットの情報を取得
			packet_head, binary_size = packets_info.pop()
			#print("size",packet_head, binary_size)
			# パケットから画像のバイナリを取得
			img_bytes = self.buff[packet_head + self.PACKET_HEADER_SIZE+self.PACKET_NAME_SIZE:packet_head + self.PACKET_HEADER_SIZE + binary_size+self.PACKET_NAME_SIZE]
			# バッファから不要なバイナリを削除
			self.buff = self.buff[packet_head + self.PACKET_HEADER_SIZE + binary_size+self.PACKET_NAME_SIZE:]
			
			# 画像をバイナリから復元
			img = np.frombuffer(img_bytes, dtype=np.uint8)
			img = cv2.imdecode(img, 1)
			# 画像を表示用に加工
			img = cv2.flip(img, 0)

			img = cv2.resize(img, (self.VIEW_WIDTH, self.VIEW_HEIGHT))
			# 画像をバイナリに変換
			img = img.tostring()

			# 作成した画像をテクスチャに設定
			
			img_texture = Texture.create(size=(self.VIEW_WIDTH, self.VIEW_HEIGHT), colorfmt='rgb')
			#img_texture = Texture.create(size=(400, 600), colorfmt='rgb')
			img_texture.blit_buffer(img, colorfmt='rgb', bufferfmt='ubyte')
			self.ids.image_source.texture=img_texture
			#self.texture = img_texture
			
			#SendMessage Creattion
			send_mes="loop:".ljust(self.PACKET_CLIENT_SIZE)
			if self.sendflag_regname:
				send_mes=("reg_name:"+self.reg_name).ljust(self.PACKET_CLIENT_SIZE)
				self.sendflag_regname=False
			elif self.sendflag_registration:
				send_mes=("registration:").ljust(self.PACKET_CLIENT_SIZE)
				self.sendflag_registration=False

			self.soc.sendall(send_mes.encode())
			#self.soc.sendall(b'recv')
			
		'''
		ret,frame=self.cap.read()
		image_texture = Texture.create(size=(frame.shape[1], frame.shape[0]), colorfmt='bgr')
		image_texture.blit_buffer(frame.tostring(), colorfmt='bgr', bufferfmt='ubyte')
		self.ids.image_source.texture=image_texture
		#print('ret',ret)
		'''


	def close(self):
		App.get_running_app().stop()

	def setting(self):
		box = GridLayout(cols = 1)
			
		#box.add_widget(Label(text="Name: ", bold = True))
		self.st = TextInput(id= "serverText")
		box.add_widget(self.st)

		'''
		box.add_widget(Label(text="Port: ", bold = True))
		self.pt = TextInput(id= "portText")
		box.add_widget(self.pt)
		'''

		btn = Button(text="Set", bold=True)
		btn.bind(on_press=self.settingProcess)
		box.add_widget(btn)
		self.popup = Popup(title='Registration',content=box,size_hint=(.6,.4))
		self.popup.open()

	def settingIP(self):
		box = GridLayout(cols = 2)
		box.add_widget(Label(text="IpAddress: ", bold = True))
		self.st2 = TextInput(id= "serverText")
		self.st2.text=self.ipAddress
		box.add_widget(self.st2)
		btn = Button(text="Set", bold=True)
		btn.bind(on_press=self.settingProcess2)
		box.add_widget(btn)
		self.popup = Popup(title='Settings',content=box,size_hint=(.6,.4))
		self.popup.open()

	def settingProcess(self, btn):
		try:
			self.reg_name = self.st.text
			self.sendflag_regname=True
		except:
			pass
		print(self.reg_name)
		self.popup.dismiss()


	def settingProcess2(self, btn):
		try:
			self.ipAddress = self.st2.text
		except:
			pass
		print(self.ipAddress)
		self.popup.dismiss()

	def registration(self):
		self.sendflag_registration=True

class videoStreamApp(App):
	def build(self):
		return Builder.load_string(kv)
	

videoStreamApp().run()
