import random
import socket
import time
from _thread import *
import threading
from datetime import datetime
import json

clients_lock = threading.Lock()
connected = 0

clients = {}

def connectionLoop(sock):
   while True:
      data, addr = sock.recvfrom(1024)
      data = str(data)
      data = data[2:-1]
     
      if addr in clients:
         if 'heartbeat' in data:
            clients[addr]['lastBeat'] = datetime.now()
         else:
            playerInfo = json.loads(data)
            clients[addr]['position'] = playerInfo['position']
            clients[addr]['rotation'] = playerInfo['rotation']
      else:
         if 'connect' in data:
            clients[addr] = {}
            clients[addr]['lastBeat'] = datetime.now()
            clients[addr]['color'] = 0
            clients[addr]['position'] = {}
            clients[addr]['rotation'] = {}
            message = {"cmd": 0,"player":[{"id":str(addr)}]}
            clientList = {"cmd": 2,"player":[]}
            m = json.dumps(message)
            for c in clients:
               if addr != c:
                  sock.sendto(bytes(m,'utf8'), (c[0],c[1]))
                  clientList['player'].append({"id":str(c)})
            m = json.dumps(clientList)
            sock.sendto(bytes(m,'utf8'), (addr[0],addr[1]))
            message["cmd"] = 4
            m = json.dumps(message)
            sock.sendto(bytes(m,'utf8'), (addr[0],addr[1]))

def cleanClients(sock):
   while True:
      cleared = False
      message = {"cmd": 3,"player":[]}
      for c in list(clients.keys()):
         if (datetime.now() - clients[c]['lastBeat']).total_seconds() > 5:
            print('Dropped Client: ', c)
            clients_lock.acquire()
            del clients[c]
            clients_lock.release()
            message['player'].append({"id":str(c)})
            cleared = True
      m = json.dumps(message)
      if cleared:
         for c in clients:
            sock.sendto(bytes(m,'utf8'), (c[0],c[1]))
      time.sleep(1)

def gameLoop(sock):
   while True:
      GameState = {"cmd": 1, "players": []}
      clients_lock.acquire()
      print (clients)
      for c in clients:
         player = {}
         clients[c]['color'] = {"R": random.random(), "G": random.random(), "B": random.random()}
         player['id'] = str(c)
         player['color'] = clients[c]['color']
         player['position'] = clients[c]['position']
         player['rotation'] = clients[c]['rotation']
         GameState['players'].append(player)
      s=json.dumps(GameState)
      print(s)
      for c in clients:
         sock.sendto(bytes(s,'utf8'), (c[0],c[1]))
      clients_lock.release()
      time.sleep(1/10)

def main():
   port = 12345
   s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
   s.bind(('', port))
   start_new_thread(gameLoop, (s,))
   start_new_thread(connectionLoop, (s,))
   start_new_thread(cleanClients,(s,))
   while True:
      time.sleep(1)

if __name__ == '__main__':
   main()