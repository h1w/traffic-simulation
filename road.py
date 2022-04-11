from audioop import add
import time
import board
import neopixel

import graph as gr

import itertools
i_counter = itertools.count()

import json
import random

import threading
import signal
import sys

import asyncio, socket

server_addr = '0.0.0.0'
server_port = 8000

import logging

logging.basicConfig(
    filename='traffic.log',
    filemod='a',
    format='%(asctime)s %(lineno)d %(levelname)s:%(message)s',
    level=logging.DEBUG
)
logger = logging.getLogger(__name__)

NUM_PIXELS = 24*12 + 24*16 + 24*12 + 22*20 # Crossroad 1 = 24*12 pixels, crossroad 2 = 24*16 pixels, crossroad 3 = 24*12 pixels, crossroad 4 = 22*20
PIXEL_PIN = board.D18
ORDER = neopixel.RGB
BRIGHTNESS = 0.5

CAR_AMOUNT = 220

car_count_answer = None
traffic_control = None

car_completed_routes = 0

class AddressLedStrip:
    def __init__(self, num_pixels, pixel_pin, order, brightness):
        self.num_pixels = num_pixels
        self.pixel_pin = pixel_pin
        self.order = order
        self.brightness = brightness

        self.pixels = neopixel.NeoPixel(
            self.pixel_pin, self.num_pixels, brightness=self.brightness, auto_write=False, pixel_order=self.order
        )

    def ClearPixels(self):
        for i in range(self.num_pixels):
            self.pixels[i] = (0, 0, 0)
        self.pixels.show()
    
    def DisplayPixels(self, crossroad_road):
        for i in range(self.num_pixels):
            if crossroad_road[i] != None:
                self.pixels[i] = crossroad_road[i].color
            else:
                self.pixels[i] = (0, 0, 0)
        self.pixels.show()

class Car:
    def __init__(self, color, pos_start, pos_finish, max_speed, acceleration, movement_way):
        self.id = next(i_counter)
        self.color = color
        self.pos = 0
        self.pos_start = pos_start
        self.pos_finish = pos_finish
        self.max_speed = max_speed
        self.acceleration = acceleration
        self.movement_way = movement_way
        self.road_line = 0

class TrafficLight:
    def __init__(self, pos, color="green"):
        self.pos = pos
        self.color = color
    
    def SetColor(self, color):
        self.color = color

    def GetColor(self, color):
        return self.color

class TrafficSimulation:
    def __init__(self):
        # Add crossroad nodes
        self.nodes = []
        for node in range(0, NUM_PIXELS):
            self.nodes.append(gr.Node(node))
        
        #### Create self.graph ###
        self.graph = gr.Graph.create_from_nodes(self.nodes)
        
        # Crossroad 1

        # Connect self.nodes like road
        # 1
        for node in range(0, 23):
            self.graph.connect(self.nodes[node], self.nodes[node+1])
        # 2
        for node in range(24, 47):
            self.graph.connect(self.nodes[node], self.nodes[node+1])
        # 3
        for node in range(71, 48, -1):
            self.graph.connect(self.nodes[node], self.nodes[node-1])
        # 4
        for node in range(95, 72, -1):
            self.graph.connect(self.nodes[node], self.nodes[node-1])
        # 5
        for node in range(96, 119):
            self.graph.connect(self.nodes[node], self.nodes[node+1])
        # 6
        for node in range(120, 143):
            self.graph.connect(self.nodes[node], self.nodes[node+1])
        # 7
        for node in range(167, 144, -1):
            self.graph.connect(self.nodes[node], self.nodes[node-1])
        # 8
        for node in range(191, 168, -1):
            self.graph.connect(self.nodes[node], self.nodes[node-1])
        # 9
        for node in range(192, 215):
            self.graph.connect(self.nodes[node], self.nodes[node+1])
        # 10
        for node in range(216, 239):
            self.graph.connect(self.nodes[node], self.nodes[node+1])
        # 11
        for node in range(240, 263):
            self.graph.connect(self.nodes[node], self.nodes[node+1])
        # 12
        for node in range(264, 287):
            self.graph.connect(self.nodes[node], self.nodes[node+1])
        
        # Connect crossroad nodes
        # 1
        self.graph.connect(self.nodes[23], self.nodes[24]) # 1-2
        self.graph.connect(self.nodes[23], self.nodes[167]) # 1-7
        self.graph.connect(self.nodes[23], self.nodes[216]) # 1-10

        # 4
        self.graph.connect(self.nodes[72], self.nodes[216]) # 4-10
        self.graph.connect(self.nodes[72], self.nodes[264]) # 4-12
        # 5
        self.graph.connect(self.nodes[119], self.nodes[120]) # 5-6
        # 8
        self.graph.connect(self.nodes[168], self.nodes[71]) # 8-3
        self.graph.connect(self.nodes[168], self.nodes[264]) # 8-12
        # 9
        self.graph.connect(self.nodes[215], self.nodes[216]) # 9-10

        # 11
        self.graph.connect(self.nodes[263], self.nodes[167]) # 11-7
        self.graph.connect(self.nodes[263], self.nodes[71]) # 11-3
        self.graph.connect(self.nodes[263], self.nodes[264]) # 11-12        

        # Connect ends of roads to each other
        self.graph.connect(self.nodes[287], self.nodes[0])
        # self.graph.connect(self.nodes[47], self.nodes[95])
        # self.graph.connect(self.nodes[48], self.nodes[96])
        # self.graph.connect(self.nodes[143], self.nodes[191])
        # self.graph.connect(self.nodes[144], self.nodes[192])
        self.graph.connect(self.nodes[239], self.nodes[240])

        # Crossroad 2
        ppa = 24*12 # prev_pix_amount

        # Connect new crossroad with previous crossroad
        self.graph.connect(self.nodes[335+ppa], self.nodes[96])
        self.graph.connect(self.nodes[336+ppa], self.nodes[95])
        self.graph.connect(self.nodes[48], self.nodes[383+ppa])
        self.graph.connect(self.nodes[47], self.nodes[0+ppa])

        # Connect self.nodes like road
        # 1
        for node in range(0+ppa, 23+ppa):
            self.graph.connect(self.nodes[node], self.nodes[node+1])
        # 2
        for node in range(24+ppa, 47+ppa):
            self.graph.connect(self.nodes[node], self.nodes[node+1])
        # 3
        for node in range(71+ppa, 48+ppa, -1):
            self.graph.connect(self.nodes[node], self.nodes[node-1])
        # 4
        for node in range(95+ppa, 72+ppa, -1):
            self.graph.connect(self.nodes[node], self.nodes[node-1])
        # 5
        for node in range(96+ppa, 119+ppa):
            self.graph.connect(self.nodes[node], self.nodes[node+1])
        # 6
        for node in range(120+ppa, 143+ppa):
            self.graph.connect(self.nodes[node], self.nodes[node+1])
        # 7
        for node in range(167+ppa, 144+ppa, -1):
            self.graph.connect(self.nodes[node], self.nodes[node-1])
        # 8
        for node in range(191+ppa, 168+ppa, -1):
            self.graph.connect(self.nodes[node], self.nodes[node-1])
        # 9
        for node in range(192+ppa, 215+ppa):
            self.graph.connect(self.nodes[node], self.nodes[node+1])
        # 10
        for node in range(216+ppa, 239+ppa):
            self.graph.connect(self.nodes[node], self.nodes[node+1])
        # 11
        for node in range(263+ppa, 240+ppa, -1):
            self.graph.connect(self.nodes[node], self.nodes[node-1])
        # 12
        for node in range(287+ppa, 264+ppa, -1):
            self.graph.connect(self.nodes[node], self.nodes[node-1])
        # 13
        for node in range(288+ppa, 311+ppa):
            self.graph.connect(self.nodes[node], self.nodes[node+1])
        # 14
        for node in range(312+ppa, 335+ppa):
            self.graph.connect(self.nodes[node], self.nodes[node+1])
        # 15
        for node in range(359+ppa, 336+ppa, -1):
            self.graph.connect(self.nodes[node], self.nodes[node-1])
        # 16
        for node in range(383+ppa, 360+ppa, -1):
            self.graph.connect(self.nodes[node], self.nodes[node-1])
        
        # Connect crossroad nodes
        # 1
        self.graph.connect(self.nodes[23+ppa], self.nodes[24+ppa])
        self.graph.connect(self.nodes[23+ppa], self.nodes[120+ppa])
        # 4
        self.graph.connect(self.nodes[72+ppa], self.nodes[359+ppa])
        self.graph.connect(self.nodes[72+ppa], self.nodes[263+ppa])
        # 5
        self.graph.connect(self.nodes[119+ppa], self.nodes[216+ppa])
        self.graph.connect(self.nodes[119+ppa], self.nodes[120+ppa])
        # 8
        self.graph.connect(self.nodes[168+ppa], self.nodes[71+ppa])
        self.graph.connect(self.nodes[168+ppa], self.nodes[359+ppa])
        # 9
        self.graph.connect(self.nodes[215+ppa], self.nodes[312+ppa])
        self.graph.connect(self.nodes[215+ppa], self.nodes[216+ppa])
        # 13
        self.graph.connect(self.nodes[264+ppa], self.nodes[167+ppa])
        self.graph.connect(self.nodes[264+ppa], self.nodes[71+ppa])
        # 14
        self.graph.connect(self.nodes[311+ppa], self.nodes[312+ppa])
        self.graph.connect(self.nodes[311+ppa], self.nodes[24+ppa])
        # 16
        self.graph.connect(self.nodes[360+ppa], self.nodes[263+ppa])
        self.graph.connect(self.nodes[360+ppa], self.nodes[167+ppa])
               

        # Connect ends of roads to each other
        self.graph.connect(self.nodes[47+ppa], self.nodes[95+ppa])
        self.graph.connect(self.nodes[48+ppa], self.nodes[96+ppa])
        self.graph.connect(self.nodes[143+ppa], self.nodes[191+ppa])
        self.graph.connect(self.nodes[144+ppa], self.nodes[192+ppa])
        # self.graph.connect(self.nodes[239+ppa], self.nodes[287+ppa])
        # self.graph.connect(self.nodes[240+ppa], self.nodes[288+ppa])
        # self.graph.connect(self.nodes[335+ppa], self.nodes[383+ppa])
        # self.graph.connect(self.nodes[336+ppa], self.nodes[0+ppa])

        # Crossroad 3
        ppa2 = ppa + 24*16 # prev_pix_amount

        # Connect new crossroad with previous crossroad
        self.graph.connect(self.nodes[96+ppa2], self.nodes[288+ppa])
        self.graph.connect(self.nodes[95+ppa2], self.nodes[287+ppa])
        self.graph.connect(self.nodes[240+ppa], self.nodes[48+ppa2])
        self.graph.connect(self.nodes[239+ppa], self.nodes[47+ppa2])

        # Connect self.nodes like road
        # 1
        for node in range(144+ppa2, 167+ppa2):
            self.graph.connect(self.nodes[node], self.nodes[node+1])
        # 2
        for node in range(143+ppa2, 120+ppa2, -1):
            self.graph.connect(self.nodes[node], self.nodes[node-1])
        # 3
        for node in range(119+ppa2, 96+ppa2, -1):
            self.graph.connect(self.nodes[node], self.nodes[node-1])
        # 4
        for node in range(72+ppa2, 95+ppa2):
            self.graph.connect(self.nodes[node], self.nodes[node+1])
        # 5
        for node in range(48+ppa2, 71+ppa2):
            self.graph.connect(self.nodes[node], self.nodes[node+1])
        # 6
        for node in range(47+ppa2, 24+ppa2, -1):
            self.graph.connect(self.nodes[node], self.nodes[node-1])
        # 7
        for node in range(23+ppa2, 0+ppa2, -1):
            self.graph.connect(self.nodes[node], self.nodes[node-1])
        # 8
        for node in range(264+ppa2, 287+ppa2):
            self.graph.connect(self.nodes[node], self.nodes[node+1])
        # 9
        for node in range(240+ppa2, 263+ppa2):
            self.graph.connect(self.nodes[node], self.nodes[node+1])
        # 10
        for node in range(239+ppa2, 216+ppa2, -1):
            self.graph.connect(self.nodes[node], self.nodes[node-1])
        # 11
        for node in range(215+ppa2, 192+ppa2, -1):
            self.graph.connect(self.nodes[node], self.nodes[node-1])
        # 12
        for node in range(168+ppa2, 191+ppa2):
            self.graph.connect(self.nodes[node], self.nodes[node+1])
        
        # Connect crossroad nodes
        #
        self.graph.connect(self.nodes[167+ppa2], self.nodes[264+ppa2])
        #
        self.graph.connect(self.nodes[120+ppa2], self.nodes[119+ppa2])
        self.graph.connect(self.nodes[120+ppa2], self.nodes[23+ppa2])
        #
        self.graph.connect(self.nodes[71+ppa2], self.nodes[168+ppa2])
        #
        self.graph.connect(self.nodes[24+ppa2], self.nodes[23+ppa2])
        #
        self.graph.connect(self.nodes[263+ppa2], self.nodes[72+ppa2])
        self.graph.connect(self.nodes[263+ppa2], self.nodes[168+ppa2])
        #
        self.graph.connect(self.nodes[216+ppa2], self.nodes[215+ppa2])
               

        # Connect ends of roads to each other
        # self.graph.connect(self.nodes[192+ppa2], self.nodes[144+ppa2])
        # self.graph.connect(self.nodes[191+ppa2], self.nodes[143+ppa2])
        #
        self.graph.connect(self.nodes[0+ppa2], self.nodes[240+ppa2])
        self.graph.connect(self.nodes[287+ppa2], self.nodes[239+ppa2])

        # Crossroad 4
        ppa3 = ppa2 + 24*12 # prev_pix_amount

        # Connect new crossroad with previous crossroad
        # with crossroad 3
        self.graph.connect(self.nodes[43+ppa3], self.nodes[143+ppa2])
        self.graph.connect(self.nodes[44+ppa3], self.nodes[144+ppa2])
        self.graph.connect(self.nodes[191+ppa2], self.nodes[87+ppa3])
        self.graph.connect(self.nodes[192+ppa2], self.nodes[88+ppa3])
        # with crossroad 1
        self.graph.connect(self.nodes[143], self.nodes[0+ppa3])
        self.graph.connect(self.nodes[144], self.nodes[439+ppa3])
        self.graph.connect(self.nodes[395+ppa3], self.nodes[192])
        self.graph.connect(self.nodes[396+ppa3], self.nodes[191])

        # Connect self.nodes like road
        ###
        for node in range(439+ppa3, 418+ppa3, -1):
            self.graph.connect(self.nodes[node], self.nodes[node-1])
        
        for node in range(0+ppa3, 21+ppa3):
            self.graph.connect(self.nodes[node], self.nodes[node+1])
        ###
        for node in range(22+ppa3, 43+ppa3):
            self.graph.connect(self.nodes[node], self.nodes[node+1])

        for node in range(65+ppa3, 44+ppa3, -1):
            self.graph.connect(self.nodes[node], self.nodes[node-1])
        ###
        for node in range(87+ppa3, 66+ppa3, -1):
            self.graph.connect(self.nodes[node], self.nodes[node-1])
        
        for node in range(88+ppa3, 109+ppa3):
            self.graph.connect(self.nodes[node], self.nodes[node+1])
        ###
        for node in range(110+ppa3, 131+ppa3):
            self.graph.connect(self.nodes[node], self.nodes[node+1])

        for node in range(153+ppa3, 132+ppa3, -1):
            self.graph.connect(self.nodes[node], self.nodes[node-1])
        
        for node in range(154+ppa3, 175+ppa3):
            self.graph.connect(self.nodes[node], self.nodes[node+1])
        ###
        for node in range(176+ppa3, 197+ppa3):
            self.graph.connect(self.nodes[node], self.nodes[node+1])

        for node in range(219+ppa3, 198+ppa3, -1):
            self.graph.connect(self.nodes[node], self.nodes[node-1])
        
        for node in range(220+ppa3, 241+ppa3):
            self.graph.connect(self.nodes[node], self.nodes[node+1])
        ###
        for node in range(242+ppa3, 263+ppa3):
            self.graph.connect(self.nodes[node], self.nodes[node+1])
        
        for node in range(285+ppa3, 264+ppa3, -1):
            self.graph.connect(self.nodes[node], self.nodes[node-1])
        
        for node in range(286+ppa3, 307+ppa3):
            self.graph.connect(self.nodes[node], self.nodes[node+1])
        ###
        for node in range(308+ppa3, 329+ppa3):
            self.graph.connect(self.nodes[node], self.nodes[node+1])
        
        for node in range(351+ppa3, 330+ppa3, -1):
            self.graph.connect(self.nodes[node], self.nodes[node-1])
        
        for node in range(352+ppa3, 373+ppa3):
            self.graph.connect(self.nodes[node], self.nodes[node+1])
        ###
        for node in range(374+ppa3, 395+ppa3):
            self.graph.connect(self.nodes[node], self.nodes[node+1])
        
        for node in range(417+ppa3, 396+ppa3, -1):
            self.graph.connect(self.nodes[node], self.nodes[node-1])
        
        # Connect crossroad nodes
        #
        self.graph.connect(self.nodes[418+ppa3], self.nodes[286+ppa3])
        self.graph.connect(self.nodes[418+ppa3], self.nodes[154+ppa3])
        self.graph.connect(self.nodes[21+ppa3], self.nodes[153+ppa3])
        self.graph.connect(self.nodes[21+ppa3], self.nodes[22+ppa3])
        #
        self.graph.connect(self.nodes[66+ppa3], self.nodes[417+ppa3])
        self.graph.connect(self.nodes[66+ppa3], self.nodes[286+ppa3])
        self.graph.connect(self.nodes[109+ppa3], self.nodes[285+ppa3])
        self.graph.connect(self.nodes[109+ppa3], self.nodes[110+ppa3])
        #
        self.graph.connect(self.nodes[197+ppa3], self.nodes[65+ppa3])
        self.graph.connect(self.nodes[197+ppa3], self.nodes[417+ppa3])
        self.graph.connect(self.nodes[198+ppa3], self.nodes[374+ppa3])
        self.graph.connect(self.nodes[241+ppa3], self.nodes[242+ppa3])
        #
        self.graph.connect(self.nodes[329+ppa3], self.nodes[154+ppa3])
        self.graph.connect(self.nodes[329+ppa3], self.nodes[65+ppa3])
        self.graph.connect(self.nodes[330+ppa3], self.nodes[22+ppa3])
        self.graph.connect(self.nodes[373+ppa3], self.nodes[374+ppa3])

        # Connect ends of roads to each other
        self.graph.connect(self.nodes[263+ppa3], self.nodes[308+ppa3])
        self.graph.connect(self.nodes[264+ppa3], self.nodes[351+ppa3])
        self.graph.connect(self.nodes[307+ppa3], self.nodes[352+ppa3])
        #
        self.graph.connect(self.nodes[131+ppa3], self.nodes[176+ppa3])
        self.graph.connect(self.nodes[132+ppa3], self.nodes[219+ppa3])
        self.graph.connect(self.nodes[175+ppa3], self.nodes[220+ppa3])

        # Array for pixel displaying
        self.crossroad_road = [None] * NUM_PIXELS

        self.cars = []

        # Traffic Lights
        self.traffic_lights = {
            # Crossroad 1
            23: TrafficLight(23, "red"),
            72: TrafficLight(72, "green"),
            119: TrafficLight(119, "green"),
            168: TrafficLight(168, "red"),
            215: TrafficLight(215, "red"),
            263: TrafficLight(263, "green"),

            # Crossroad 2
            23+ppa: TrafficLight(23+ppa, "red"),
            72+ppa: TrafficLight(72+ppa, "green"),
            119+ppa: TrafficLight(119+ppa, "green"),
            168+ppa: TrafficLight(168+ppa, "red"),
            215+ppa: TrafficLight(215+ppa, "red"),
            264+ppa: TrafficLight(264+ppa, "green"),
            311+ppa: TrafficLight(311+ppa, "green"),
            360+ppa: TrafficLight(360+ppa, "red"),

            # Crossroad 3
            167+ppa2: TrafficLight(267+ppa2, "green"),
            120+ppa2: TrafficLight(120+ppa2, "green"),
            71+ppa2: TrafficLight(71+ppa2, "red"),
            24+ppa2: TrafficLight(24+ppa2, "red"),
            263+ppa2: TrafficLight(240+ppa2, "green"),
            216+ppa2: TrafficLight(216+ppa2, "green"),

            # Crossroad 4
            418+ppa3: TrafficLight(418+ppa3, "green"),
            21+ppa3: TrafficLight(21+ppa3, "green"),
            
            66+ppa3: TrafficLight(66+ppa3, "red"),
            109+ppa3: TrafficLight(109+ppa3, "red"),
            
            197+ppa3: TrafficLight(197+ppa3, "green"),
            198+ppa3: TrafficLight(198+ppa3, "green"),
            241+ppa3: TrafficLight(241+ppa3, "green"),
            
            329+ppa3: TrafficLight(329+ppa3, "red"),
            330+ppa3: TrafficLight(330+ppa3, "red"),
            373+ppa3: TrafficLight(373+ppa3, "red"),
        }

    
    def AddNewCar(self, car):
        if self.crossroad_road[car.pos_start] == None:
            self.crossroad_road[car.pos_start] = car
            self.cars.append(car)
    
    def CarsMovement(self):
        for car in self.cars:

            # The car has completed its route
            if car.pos == len(car.movement_way):
                self.crossroad_road[car.movement_way[car.pos-1]] = None
                
                self.cars.remove(car) # remove car from cars list
                global car_completed_routes
                car_completed_routes += 1
                continue
            elif car.pos == 0:
                self.crossroad_road[car.movement_way[car.pos]] = car
                self.cars[self.cars.index(car)].pos += 1
            elif car.pos > 0:
                if self.crossroad_road[car.movement_way[car.pos]] == None:
                    # Check Traffic Lights
                    if car.movement_way[car.pos] in self.traffic_lights.keys() and self.traffic_lights[car.movement_way[car.pos]].color == "red":
                        continue
                    else:
                        self.crossroad_road[car.movement_way[car.pos-1]] = None
                        self.crossroad_road[car.movement_way[car.pos]] = car
                        self.cars[self.cars.index(car)].pos += 1
    
    def FindBestWay(self, start, finish):
        best_way = None
        for weight, nodes in self.graph.dijkstra(self.nodes[start]):
            way = []
            for node in nodes:
                way.append(node.data)
            if finish in way:
                best_way = way[0:way.index(finish)+1]
                break
        if best_way == None:
            return None
        else:
            return best_way
        
    def RoadLines(self, car_id, car_pos):
        ppa = 24*12
        ppa2 = ppa + 24*16
        ppa3 = ppa2 + 24*12

        if car_pos >= 216+ppa2 and car_pos <= 239+ppa2: # A1
            # self.road_lines[1].append(car_id)
            return 1
        elif car_pos >= 240+ppa2 and car_pos <= 263+ppa2: # A2
            # self.road_lines[2].append(car_id)
            return 2
        elif car_pos >= 24+ppa2 and car_pos <= 47+ppa2: # A3
            # self.road_lines[3].append(car_id)
            return 3
        elif car_pos >= 48+ppa2 and car_pos <= 71+ppa2: # A4
            # self.road_lines[4].append(car_id)
            return 4
        elif car_pos >= 120+ppa2 and car_pos <= 143+ppa2: # A5
            # self.road_lines[5].append(car_id)
            return 5
        elif car_pos >= 144+ppa2 and car_pos <= 167+ppa2: # A6
            # self.road_lines[6].append(car_id)
            return 6

        elif car_pos >= 192+ppa and car_pos <= 215+ppa: # A7
            # self.road_lines[7].append(car_id)
            return 7
        elif car_pos >= 168+ppa and car_pos <= 191+ppa: # A8
            # self.road_lines[8].append(car_id)
            return 8
        elif car_pos >= 96+ppa and car_pos <= 119+ppa: # A9
            # self.road_lines[9].append(car_id)
            return 9
        elif car_pos >= 72+ppa and car_pos <= 95+ppa: # A10
            # self.road_lines[10].append(car_id)
            return 10
        elif car_pos >= 0+ppa and car_pos <= 23+ppa: # A11
            # self.road_lines[11].append(car_id)
            return 11
        elif car_pos >= 360+ppa and car_pos <= 383+ppa: # A12
            # self.road_lines[12].append(car_id)
            return 12
        elif car_pos >= 288+ppa and car_pos <= 311+ppa: # A13
            # self.road_lines[13].append(car_id)
            return 13
        elif car_pos >= 264+ppa and car_pos <= 287+ppa: # A14
            # self.road_lines[14].append(car_id)
            return 14
        
        elif car_pos >= 96 and car_pos <= 119: # A15
            # self.road_lines[15].append(car_id)
            return 15
        elif car_pos >= 72 and car_pos <= 95: # A16
            # self.road_lines[16].append(car_id)
            return 16
        elif car_pos >= 0 and car_pos <= 23: # A17
            # self.road_lines[17].append(car_id)
            return 17
        elif car_pos >= 240 and car_pos <= 263: # A18
            # self.road_lines[18].append(car_id)
            return 18
        elif car_pos >= 192 and car_pos <= 215: # A19
            # self.road_lines[19].append(car_id)
            return 19
        elif car_pos >= 168 and car_pos <= 191: # A20
            # self.road_lines[20].append(car_id)
            return 20
        
        elif car_pos >= 88+ppa3 and car_pos <= 109+ppa3: # A21
            # self.road_lines[21].append(car_id)
            return 21
        elif car_pos >= 66+ppa3 and car_pos <= 87+ppa3: # A22
            # self.road_lines[22].append(car_id)
            return 22
        elif car_pos >= 0+ppa3 and car_pos <= 21+ppa3: # A23
            # self.road_lines[23].append(car_id)
            return 23
        elif car_pos >= 418+ppa3 and car_pos <= 439+ppa3: # A24
            # self.road_lines[24].append(car_id)
            return 24
        elif car_pos >= 352+ppa3 and car_pos <= 373+ppa3: # A25
            # self.road_lines[25].append(car_id)
            return 25
        elif car_pos >= 330+ppa3 and car_pos <= 351+ppa3: # A26
            # self.road_lines[26].append(car_id)
            return 26
        elif car_pos >= 308+ppa3 and car_pos <= 329+ppa3: # A27
            # self.road_lines[27].append(car_id)
            return 27
        elif car_pos >= 220+ppa3 and car_pos <= 241+ppa3: # A28
            # self.road_lines[28].append(car_id)
            return 28
        elif car_pos >= 198+ppa3 and car_pos <= 219+ppa3: # A29
            # self.road_lines[29].append(car_id)
            return 29
        elif car_pos >= 176+ppa3 and car_pos <= 197+ppa3: # A30
            # self.road_lines[30].append(car_id)
            return 30
        
        return 0
    
    def ChangeTrafficLightColor(self, pos, color):
        self.traffic_lights[pos].color = color


address_led_strip = AddressLedStrip(NUM_PIXELS, PIXEL_PIN, ORDER, BRIGHTNESS)

address_led_strip.ClearPixels() # Clear address led strip before work

crossroad = TrafficSimulation()

# Add car
def AddCar(color, pos_start, pos_finish, max_speed, acceleration, movement_way):
    car = Car(color, pos_start, pos_finish, max_speed, acceleration, movement_way)
    crossroad.AddNewCar(car)

ppa = 24*12
ppa2 = ppa + 24*16
ppa3 = ppa2 + 24*12

best_ways = []

# Uncomment to generate ways again
# spawn_start = [0, 240, ppa+95, ppa+96, ppa+191, ppa+192, ppa2+240, ppa2+239, 308+ppa3, 351+ppa3, 352+ppa3, 220+ppa3, 219+ppa3, 176+ppa3]
# spawn_finish = [287, 239, ppa+47, ppa+48, ppa+143, ppa+144, ppa2+287, ppa2+0, 175+ppa3, 132+ppa3, 131+ppa3, 263+ppa3, 264+ppa3, 307+ppa3]

# logging.info('There is a search and generation of the shortest paths for traffic.')
# logging.info('This may take some time (about 1-2 minutes)\n')
# for sp_start in spawn_start:
#     for sp_finish in spawn_finish:
#         best_way = crossroad.FindBestWay(sp_start, sp_finish)
#         if best_way != None:
#             best_ways.append(best_way)
# logging.info('Generation done.\n')
# with open('shortest_ways.txt', 'w') as f:
#     f.write(json.dumps(best_ways))

# Use pregenerated best ways
logging.info('Using pregenerated best ways.\n')
with open('pregenerated_shortest_ways.txt', 'r') as f:
    best_ways = json.loads(f.read())

# Start new thread for traffic lights
traffic_lights_control_thread_alive = True
def trafficLightsControl():
    global traffic_control
    global red_signal_telemetry

    logging.info("Traffic Lights loop has been started.\n")
    ppa = 24*12
    ppa2 = ppa + 24*16
    ppa3 = ppa2 + 24*12
    timing = time.time()
    ok = False

    while traffic_lights_control_thread_alive:
        if time.time() - timing > 1.0:
            try:
                timing = time.time()

                if traffic_control != None:
                    traffic_control_tmp = traffic_control

                    traffic_control_tmp = traffic_control_tmp.split('|')[1:]

                    for traffic_light in traffic_control_tmp:
                        key = traffic_light.split(':')[0]
                        value = traffic_light.split(':')[1]

                        # Crossroad 3
                        if key == "A1":
                            crossroad.ChangeTrafficLightColor(216+ppa2, value)
                        elif key == "A2":
                            crossroad.ChangeTrafficLightColor(263+ppa2, value)
                        elif key == "A3":
                            crossroad.ChangeTrafficLightColor(24+ppa2, value)
                        elif key == "A4":
                            crossroad.ChangeTrafficLightColor(71+ppa2, value)
                        elif key == "A5":
                            crossroad.ChangeTrafficLightColor(120+ppa2, value)
                        elif key == "A6":
                            crossroad.ChangeTrafficLightColor(167+ppa2, value)
                        # Crossroad 2
                        elif key == "A7":
                            crossroad.ChangeTrafficLightColor(215+ppa, value)
                        elif key == "A8":
                            crossroad.ChangeTrafficLightColor(168+ppa, value)
                        elif key == "A9":
                            crossroad.ChangeTrafficLightColor(119+ppa, value)
                        elif key == "A10":
                            crossroad.ChangeTrafficLightColor(72+ppa, value)
                        elif key == "A11":
                            crossroad.ChangeTrafficLightColor(23+ppa, value)
                        elif key == "A12":
                            crossroad.ChangeTrafficLightColor(360+ppa, value)
                        elif key == "A13":
                            crossroad.ChangeTrafficLightColor(311+ppa, value)
                        elif key == "A14":
                            crossroad.ChangeTrafficLightColor(264+ppa, value)
                        # Crossroad 1
                        elif key == "A15":
                            crossroad.ChangeTrafficLightColor(119, value)
                        elif key == "A16":
                            crossroad.ChangeTrafficLightColor(72, value)
                        elif key == "A17":
                            crossroad.ChangeTrafficLightColor(23, value)
                        elif key == "A18":
                            crossroad.ChangeTrafficLightColor(263, value)
                        elif key == "A19":
                            crossroad.ChangeTrafficLightColor(215, value)
                        elif key == "A20":
                            crossroad.ChangeTrafficLightColor(168, value)
                        # Crossroad 4
                        elif key == "A21":
                            crossroad.ChangeTrafficLightColor(109+ppa3, value)
                        elif key == "A22":
                            crossroad.ChangeTrafficLightColor(66+ppa3, value)
                        elif key == "A23":
                            crossroad.ChangeTrafficLightColor(21+ppa3, value)
                        elif key == "A24":
                            crossroad.ChangeTrafficLightColor(418+ppa3, value)
                        elif key == "A25":
                            crossroad.ChangeTrafficLightColor(373+ppa3, value)
                        elif key == "A26":
                            crossroad.ChangeTrafficLightColor(330+ppa3, value)
                        elif key == "A27":
                            crossroad.ChangeTrafficLightColor(329+ppa3, value)
                        elif key == "A28":
                            crossroad.ChangeTrafficLightColor(241+ppa3, value)
                        elif key == "A29":
                            crossroad.ChangeTrafficLightColor(198+ppa3, value)
                        elif key == "A30":
                            crossroad.ChangeTrafficLightColor(197+ppa3, value)
            except Exception as e:
                pass
        
        # if time.time() - timing > 5.0:
        #     timing = time.time()
        #     if ok == True:
        #         # Crossroad 1
        #         crossroad.ChangeTrafficLightColor(23, "red")
        #         crossroad.ChangeTrafficLightColor(72, "green")
        #         crossroad.ChangeTrafficLightColor(119, "green")
        #         crossroad.ChangeTrafficLightColor(168, "red")
        #         crossroad.ChangeTrafficLightColor(215, "red")
        #         crossroad.ChangeTrafficLightColor(263, "green")
        #         # Crossroad 2
        #         crossroad.ChangeTrafficLightColor(23+ppa, "red")
        #         crossroad.ChangeTrafficLightColor(72+ppa, "green")
        #         crossroad.ChangeTrafficLightColor(119+ppa, "green")
        #         crossroad.ChangeTrafficLightColor(168+ppa, "red")
        #         crossroad.ChangeTrafficLightColor(215+ppa, "red")
        #         crossroad.ChangeTrafficLightColor(264+ppa, "green")
        #         crossroad.ChangeTrafficLightColor(311+ppa, "green")
        #         crossroad.ChangeTrafficLightColor(360+ppa, "red")
        #         # Crossroad 3
        #         crossroad.ChangeTrafficLightColor(167+ppa2, "green")
        #         crossroad.ChangeTrafficLightColor(120+ppa2, "green")
        #         crossroad.ChangeTrafficLightColor(71+ppa2, "red")
        #         crossroad.ChangeTrafficLightColor(24+ppa2, "red")
        #         crossroad.ChangeTrafficLightColor(263+ppa2, "green")
        #         crossroad.ChangeTrafficLightColor(216+ppa2, "green")
        #         # Crossroad 4
        #         crossroad.ChangeTrafficLightColor(418+ppa3, "green")
        #         crossroad.ChangeTrafficLightColor(21+ppa3, "green")
        #         crossroad.ChangeTrafficLightColor(66+ppa3, "red")
        #         crossroad.ChangeTrafficLightColor(109+ppa3, "red")
        #         crossroad.ChangeTrafficLightColor(197+ppa3, "green")
        #         crossroad.ChangeTrafficLightColor(198+ppa3, "green")
        #         crossroad.ChangeTrafficLightColor(241+ppa3, "green")
        #         crossroad.ChangeTrafficLightColor(329+ppa3, "red")
        #         crossroad.ChangeTrafficLightColor(330+ppa3, "red")
        #         crossroad.ChangeTrafficLightColor(373+ppa3, "red")

        #         ok = False
        #     else:
        #         # Crossroad 1
        #         crossroad.ChangeTrafficLightColor(23, "green")
        #         crossroad.ChangeTrafficLightColor(72, "red")
        #         crossroad.ChangeTrafficLightColor(119, "red")
        #         crossroad.ChangeTrafficLightColor(168, "green")
        #         crossroad.ChangeTrafficLightColor(215, "green")
        #         crossroad.ChangeTrafficLightColor(263, "red")
        #         # Crossroad 2
        #         crossroad.ChangeTrafficLightColor(23+ppa, "green")
        #         crossroad.ChangeTrafficLightColor(72+ppa, "red")
        #         crossroad.ChangeTrafficLightColor(119+ppa, "red")
        #         crossroad.ChangeTrafficLightColor(168+ppa, "green")
        #         crossroad.ChangeTrafficLightColor(215+ppa, "green")
        #         crossroad.ChangeTrafficLightColor(264+ppa, "red")
        #         crossroad.ChangeTrafficLightColor(311+ppa, "red")
        #         crossroad.ChangeTrafficLightColor(360+ppa, "green")
        #         # Crossroad 3
        #         crossroad.ChangeTrafficLightColor(167+ppa2, "red")
        #         crossroad.ChangeTrafficLightColor(120+ppa2, "red")
        #         crossroad.ChangeTrafficLightColor(71+ppa2, "green")
        #         crossroad.ChangeTrafficLightColor(24+ppa2, "green")
        #         crossroad.ChangeTrafficLightColor(263+ppa2, "red")
        #         crossroad.ChangeTrafficLightColor(216+ppa2, "red")
        #         # Crossroad 4
        #         crossroad.ChangeTrafficLightColor(418+ppa3, "red")
        #         crossroad.ChangeTrafficLightColor(21+ppa3, "red")
        #         crossroad.ChangeTrafficLightColor(66+ppa3, "green")
        #         crossroad.ChangeTrafficLightColor(109+ppa3, "green")
        #         crossroad.ChangeTrafficLightColor(197+ppa3, "red")
        #         crossroad.ChangeTrafficLightColor(198+ppa3, "red")
        #         crossroad.ChangeTrafficLightColor(241+ppa3, "red")
        #         crossroad.ChangeTrafficLightColor(329+ppa3, "green")
        #         crossroad.ChangeTrafficLightColor(330+ppa3, "green")
        #         crossroad.ChangeTrafficLightColor(373+ppa3, "green")

        #         ok = True

traffic_lights_control_thread = threading.Thread(target=trafficLightsControl, args=())
traffic_lights_control_thread.start()

def PrepareResponse(road_lines, traffic_count, cars_amount, cars_amount_on_traffic_lights):
    ready_jsn = {
        # 'cars_amount': cars_amount,
        # 'cars_amount_on_traffic_lights': cars_amount_on_traffic_lights,
        'traffic_count': traffic_count,
        # 'road_lines': road_lines,
    }
    return json.dumps(ready_jsn)

# RoadLines thread
roadlines_thread_alive = True
def RoadLines_Thread():
    logging.info("RoadLines loop has been started.\n")

    while roadlines_thread_alive:
        road_lines = {}
        for i in range(1,31):
            road_lines.update( {f'A{i}': list()} )
        
        for car in crossroad.cars:
            if car.pos != len(car.movement_way):
                car.road_line = crossroad.RoadLines(car.id, car.movement_way[car.pos])
                
                if car.road_line != 0:
                    road_lines[f'A{car.road_line}'].append(car.id)

        car_count_tmp=''
        for key, value in road_lines.items():
            car_count_tmp += f'/{len(value)}*'
        global car_count_answer
        car_count_answer = car_count_tmp

        time.sleep(3)

roadlines_thread = threading.Thread(target=RoadLines_Thread, args=())
roadlines_thread.start()

# Spawn new cars thread
spawn_new_cars_thread_alive = True
def SpawnNewCars():
    logging.info("Spawn new cars loop has been started.\n")
    while spawn_new_cars_thread_alive:
        time.sleep(0.01)
        if len(crossroad.cars) < CAR_AMOUNT:
            best_way = random.choice(best_ways)
            start = best_way[0]
            finish = best_way[len(best_way)-1]
            AddCar((random.randint(0, 255), random.randint(0, 255), random.randint(0, 255)), start, finish, 15, 2, best_way)

spawn_new_cars_thread = threading.Thread(target=SpawnNewCars, args=())
spawn_new_cars_thread.start()

# Tcp Server for Elkin Software
server_addr = '0.0.0.0'
server_port = 8686

traffic_control_tcp_server_alive = True
clients = []
send_loop = True
listen_loop = True

async def PrettyTrafficControl(request):
    traffic_control_tmp = ''
    # /A1:g*/A2:r*/A3:r*/A4:g*/A6:g*/A7:r*
    l = request.split('/')[1:]
    for i in l:
        key = i.split(':')[0]
        value = i.split(':')[1].rstrip('*')
        if value == 'r':
            value = 'red'
        elif value == 'g':
            value = 'green'
        traffic_control_tmp += f'|{key}:{value}'
    global traffic_control
    traffic_control = traffic_control_tmp

async def handle_read(reader, addr):
    global listen_loop

    while listen_loop:
        data = (await reader.read(1024)).decode('utf8')
        logging.info(f'Received {data!r} from {addr!r}')
        await PrettyTrafficControl(data)

async def handle_write(writer, addr):
    global car_count_answer
    global send_loop

    while send_loop:
        await asyncio.sleep(3)

        if car_count_answer != None:
            writer.write(car_count_answer.encode('utf8'))
            await writer.drain()
            logging.info(f'Sended {car_count_answer!r} to {addr!r}')

async def handle_client(reader, writer):
    global clients

    addr = writer.get_extra_info('peername')
    logging.info(f'New client {addr!r}')

    if not clients:
        # first client is sending data
        clients.append(asyncio.create_task(handle_read(reader, addr)))
    else:
        # all other clients are receiving data every 3 seconds
        clients.append(asyncio.create_task(handle_write(writer, addr)))
    
    await clients [-1]

async def run_server():
    server = await asyncio.start_server(handle_client, server_addr, server_port)
    async with server:
        await server.serve_forever()

def TrafficControlTCPServer():
    logging.info('Traffic control TCP server has been started\n')
    asyncio.run(run_server())
    while traffic_control_tcp_server_alive:
        pass
    
traffic_control_tcp_server_thread = threading.Thread(target=TrafficControlTCPServer, args=())
traffic_control_tcp_server_thread.start()

# MainLoop thread
mainloop_thread_alive = True
def MainLoop():
    logging.info("Main loop has been started.\n")
    while mainloop_thread_alive:
        crossroad.CarsMovement()

        address_led_strip.DisplayPixels(crossroad.crossroad_road)

        time.sleep(0.03)

mainloop_thread = threading.Thread(target=MainLoop, args=())
mainloop_thread.start()

time.sleep(0.5)

# Check User Input for stop app
logging.info("For exit program use Ctrl+C\n")

def signal_handler(sig, frame):
    logging.info('\nTerminating all threads.\n')
    
    global mainloop_thread_alive
    mainloop_thread_alive = False
    logging.info('Wait for a MainLoop thread to close...')
    mainloop_thread.join()
    logging.info('MainLoop thread closed.\n')

    global spawn_new_cars_thread_alive
    spawn_new_cars_thread_alive = False
    logging.info('Wait for a SpawnNewCars thread to close... ')
    spawn_new_cars_thread.join()
    logging.info('SpawnNewCars thread closed.\n')

    global roadlines_thread_alive
    roadlines_thread_alive = False
    logging.info('Wait for a RoadLines thread to close...')
    roadlines_thread.join()
    logging.info('RoadLines thread closed.\n')

    global traffic_lights_control_thread_alive
    traffic_lights_control_thread_alive = False
    logging.info('Wait for a TrafficLightsControl thread to close...')
    traffic_lights_control_thread.join()
    logging.info('TrafficLightsControl thread closed.\n')

    address_led_strip.ClearPixels()
    logging.info('Led strip was cleared.\n')

    global car_completed_routes
    logging.info(f'[ANSWER]: Amount of cars has completed its routes: {car_completed_routes!r}\n')

    global traffic_control_tcp_server_alive
    global send_loop
    global listen_loop
    traffic_control_tcp_server_alive = False
    send_loop = False
    listen_loop = False
    logging.info('Wait for a TrafficControlTCPServer thread to close...')
    traffic_control_tcp_server_thread.join()
    logging.info('TrafficControlTCPServer thread closed.\n')

    sys.exit(0)

signal.signal(signal.SIGINT, signal_handler)
signal.pause()
