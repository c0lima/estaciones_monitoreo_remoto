#!/usr/bin/python3
#testinggggg
import io         # used to create file streams
from io import open
import fcntl      # used to access I2C parameters like addresses
import time       # used for sleep delay and timestamps
import string     # helps parse strings
import os
import board
import busio
import socket
import adafruit_ads1x15.ads1015 as ADS
from adafruit_ads1x15.analog_in import AnalogIn
import Adafruit_DHT as dht
import Adafruit_ADS1x15
import database
#from w1thermsensor import W1ThermSensor
from datetime import datetime

class AtlasI2C:
	long_timeout = 1.5         	# the timeout needed to query readings and calibrations
	short_timeout = .5         	# timeout for regular commands
	default_bus = 1         	# the default bus for I2C on the newer Raspberry Pis, certain older boards use bus 0
	default_address = 98     	# the default address for the sensor
	current_addr = default_address

	def __init__(self, address=default_address, bus=default_bus):

		self.file_read = io.open("/dev/i2c-"+str(bus), "rb", buffering=0)
		self.file_write = io.open("/dev/i2c-"+str(bus), "wb", buffering=0)

		self.set_i2c_address(address)

	def set_i2c_address(self, addr):
		I2C_SLAVE = 0x703
		fcntl.ioctl(self.file_read, I2C_SLAVE, addr)
		fcntl.ioctl(self.file_write, I2C_SLAVE, addr)
		self.current_addr = addr

	def write(self, cmd):
		cmd += "\00"
		self.file_write.write(cmd.encode('latin-1'))

	def read(self, num_of_bytes=31):
		res = self.file_read.read(num_of_bytes)         # read from the board
		if type(res[0]) is str:					# if python2 read
			response = [i for i in res if i != '\x00']
			if ord(response[0]) == 1:             # if the response isn't an error
				# change MSB to 0 for all received characters except the first and get a list of characters
				# NOTE: having to change the MSB to 0 is a glitch in the raspberry pi, and you shouldn't have to do this!
				char_list = list(map(lambda x: chr(ord(x) & ~0x80), list(response[1:])))
				return ''.join(char_list)     # convert the char list to a string and returns it
			else:
				return "Error " + str(ord(response[0]))
				
		else:									# if python3 read
			if res[0] == 1: 
				# change MSB to 0 for all received characters except the first and get a list of characters
				# NOTE: having to change the MSB to 0 is a glitch in the raspberry pi, and you shouldn't have to do this!
				char_list = list(map(lambda x: chr(x & ~0x80), list(res[1:])))
				return ''.join(char_list)     # convert the char list to a string and returns it
			else:
				return "Error " + str(res[0])

	def query(self, string):
		self.write(string)

		# the read and calibration commands require a longer timeout
		if((string.upper().startswith("R")) or
			(string.upper().startswith("CAL"))):
			time.sleep(self.long_timeout)
		elif string.upper().startswith("SLEEP"):
			return "sleep mode"
		else:
			time.sleep(self.short_timeout)

		return self.read()

	def close(self):
		self.file_read.close()
		self.file_write.close()

	def list_i2c_devices(self):
		prev_addr = self.current_addr # save the current address so we can restore it after
		i2c_devices = []
		for i in range (0,128):
			try:
				self.set_i2c_address(i)
				self.read(1)
				i2c_devices.append(i)
			except IOError:
				pass
		self.set_i2c_address(prev_addr) # restore the address we were using
		return i2c_devices

#------------------------------------------------------------------------------------------
#------------------------------------------------------------------------------------------
#------------------------------------------------------------------------------------------

def Promedio_List(Lista):
	suma = 0
	for x in range(len(Lista)):
		try:
			suma = suma + float(Lista[x])
		except:
			suma = suma + float(Lista[x].rstrip('\x00'))

	divisor = len(Lista)
	return suma/divisor

def subir_respaldo(database,query):
	try:
		db_cursor = database.cursor()
		file = open("respaldo.txt", "r")
		print("Hay archivo de respaldo")
		for linea in file.readlines():
			datos = []
			datos = linea.split("+")
			val = tuple(datos)
			db_cursor.execute(query, val)
			database.commit()
			print(db_cursor.rowcount, "Dato insertado")
			time.sleep(1)
		file.close()
		os.remove("respaldo.txt")
	except:
		print("No hay respaldo o no se ha podido subir el archivo")


def enviar_datos(database,datos,query):
	try:
		db_cursor = database.cursor()
		print(tuple(datos))
		db_cursor.execute(query, tuple(datos))
		database.commit()
		print(db_cursor.rowcount, "Dato insertado")
	except:
		print("No hay conexion a internet o algo salio mal, creando respaldo :)")

def crear_respaldo(datos):
	print("Creando respaldo :D")
	file = open("respaldo.txt", "a")
	for dato in datos:
		if dato==datos[-1]:
			file.write(str(dato) + "\n")
		else:
			file.write(str(dato) + "+")
	file.close()

def tomar_muestras(fecha,sensores,cantidad_muestras,delay):
	valores_sensores = [fecha]
	nombre_sensores = ["ORP_1","ORP_2","EC"]
	counter = 0 # para imprimir el nombre de sensores
	for sensor in sensores:
		valores = []
		'''tomar muestras'''
		for i in range(cantidad_muestras):
			valor_muestra = sensor.query("R")
			time.sleep(delay)
			print(nombre_sensores[counter],valor_muestra)
			valores.append(valor_muestra)
		promedio = "%.2f"%float(Promedio_List(valores))
		print("Promedio:",promedio)
		valores_sensores.append(promedio)
		counter+=1
	return valores_sensores


def main():

	print("==========Iniciando Sistema Calidad de Agua==============")
	dispositivo = "5.2 estacion 1"
	try:
		db = database.db
	except:
		print("No nos pudimos conectar a la DB")

	fecha = (datetime.now()).strftime("%Y-%m-%d %H:%M:%S")

	EC = AtlasI2C(100)
	ORP1 = AtlasI2C(98)
	ORP2 = AtlasI2C(108)

	cantidad_muestras = 4
	delay = 1

	sensores = [ORP1,ORP2,EC]

	query = "INSERT INTO estacion_v52_1 (fecha,orp_1,orp_2,conductividad, tds) VALUES (%s, %s, %s, %s, %s)"

	datos = tomar_muestras(fecha,sensores,cantidad_muestras,delay)
	TDS = float(datos[-1])*0.5
	print("TDS",TDS)
	datos.append("%.2f"%TDS) # Agregar TDS
	print(datos)
	try:
		subir_respaldo(db,query)
		enviar_datos(db,datos,query)
	except:
		crear_respaldo(datos)

#	os.system("sudo shutdown -h now")


if __name__ == '__main__':
	while True:
		main()
		break
