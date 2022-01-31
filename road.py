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

NUM_PIXELS = 24*12 + 24*16 + 24*12 # Crossroad 1 = 24*12 pixels, crossroad 2 = 24*16 pixels, crossroad 3 = 24*12 pixels
PIXEL_PIN = board.D18
ORDER = neopixel.RGB
BRIGHTNESS = 0.5

CAR_AMOUNT = 150

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

class TrafficLight:
    def __init__(self, pos, color="green"):
        self.pos = pos
        self.color = color
    
    def SetColor(self, color):
        self.color = color

    def GetColor(self, color):
        return self.color

class Crossroad_type1:
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
        self.graph.connect(self.nodes[143], self.nodes[191])
        self.graph.connect(self.nodes[144], self.nodes[192])
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
        self.graph.connect(self.nodes[192+ppa2], self.nodes[144+ppa2])
        self.graph.connect(self.nodes[191+ppa2], self.nodes[143+ppa2])
        #
        self.graph.connect(self.nodes[0+ppa2], self.nodes[240+ppa2])
        self.graph.connect(self.nodes[287+ppa2], self.nodes[239+ppa2])

        # Array for pixel displaying
        self.crossroad_road = [None] * NUM_PIXELS

        self.cars = []

        # Road line array
        self.road_lines = [[], [], [], [], [], [], [], [], [], [], [], [], []]

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
        }

    
    def AddNewCar(self, car):
        if self.crossroad_road[car.pos_start] == None:
            self.crossroad_road[car.pos_start] = car
            self.cars.append(car)
    
    def CarsMovement(self):
        for car in self.cars:
            # Кол-во автомобилей на конкретной полосе
            # Для вычисления лучше создать отдельный поток
            # if car.pos != len(car.movement_way):
            #     self.RoadLines(car.id, car.movement_way[car.pos])

            if car.pos == len(car.movement_way):
                self.crossroad_road[car.movement_way[car.pos-1]] = None
                
                # Remove car_id from road_lines
                for i in range(1, 13):
                    if car.id in self.road_lines[i]:
                        self.road_lines[i].remove(car.id)
                
                self.cars.remove(car) # remove car from cars list
                continue
            elif car.pos == 0:
                # if self.crossroad_road[car.movement_way[car.pos]] == None:
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

        # print(self.road_lines)
    
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
        # Check if car not in older road line, remove it
        for i in range(1, 13):
            if car_id in self.road_lines[i]:
                self.road_lines[i].remove(car_id)

        # Add car to needed road line
        if car_pos >= 0 and car_pos <= 23:
            self.road_lines[1].append(car_id)
        elif car_pos >= 24 and car_pos <= 47:
            self.road_lines[2].append(car_id)
        elif car_pos >= 48 and car_pos <= 71:
            self.road_lines[3].append(car_id)
        elif car_pos >= 72 and car_pos <= 95:
            self.road_lines[4].append(car_id)
        elif car_pos >= 96 and car_pos <= 119:
            self.road_lines[5].append(car_id)
        elif car_pos >= 120 and car_pos <= 143:
            self.road_lines[6].append(car_id)
        elif car_pos >= 144 and car_pos <= 167:
            self.road_lines[7].append(car_id)
        elif car_pos >= 168 and car_pos <= 191:
            self.road_lines[8].append(car_id)
        elif car_pos >= 192 and car_pos <= 215:
            self.road_lines[9].append(car_id)
        elif car_pos >= 216 and car_pos <= 239:
            self.road_lines[10].append(car_id)
        elif car_pos >= 240 and car_pos <= 263:
            self.road_lines[11].append(car_id)
        elif car_pos >= 264 and car_pos <= 287:
            self.road_lines[12].append(car_id)
    
    def GetRoadLines(self):
        road_lines = {
            'lines': self.road_lines[1:]
        }
        return json.dumps(road_lines)
    
    def ChangeTrafficLightColor(self, pos, color):
        self.traffic_lights[pos].color = color


address_led_strip = AddressLedStrip(NUM_PIXELS, PIXEL_PIN, ORDER, BRIGHTNESS)

address_led_strip.ClearPixels() # Clear address led strip before work

crossroad = Crossroad_type1()

# Add car
def AddCar(color, pos_start, pos_finish, max_speed, acceleration, movement_way):
    car = Car(color, pos_start, pos_finish, max_speed, acceleration, movement_way)
    crossroad.AddNewCar(car)
    # best_way = crossroad.FindBestWay(car.pos_start, car.pos_finish)
    # if best_way != None:
    #     car.movement_way = best_way
    #     crossroad.AddNewCar(car)
        # print(best_way)

# AddCar((0, 0, 255), 94, 108, 15, 2) # 1
# AddCar((255, 255, 255), 0, 200, 15, 1) # 2
# AddCar((120, 0, 0), 100, 56, 15, 5) # 3
# AddCar((0, 255, 0), 50, 0, 15, 5) # 4

ppa = 24*12
ppa2 = ppa + 24*16

# spawn_start = [0, 95, 96, 191, 192, 240]
# spawn_finish = [287, 48, 47, 143, 144, 239]
spawn_start = [0, 191, 192, 240, ppa+95, ppa+96, ppa+191, ppa+192, ppa2+144, ppa2+143, ppa2+240, ppa2+239]
spawn_finish = [287, 143, 144, 239, ppa+47, ppa+48, ppa+143, ppa+144, ppa2+192, ppa2+191, ppa2+287, ppa2+0]
best_ways = []
for sp_start in spawn_start:
    for sp_finish in spawn_finish:
        best_way = crossroad.FindBestWay(sp_start, sp_finish)
        if best_way != None:
            best_ways.append(best_way)


# AddCar((random.randint(0, 255), random.randint(0, 255), random.randint(0, 255)), random.choice(spawn_start), random.choice(spawn_finish), 15, 2)

# Start new thread for traffic lights
def restapi():
    ppa = 24*12
    ppa2 = ppa + 24*16
    timing = time.time()
    ok = False
    while True:
        if time.time() - timing > 5.0:
            print("Car amount:", len(crossroad.cars))
            timing = time.time()
            if ok == True:
                # Crossroad 1
                crossroad.ChangeTrafficLightColor(23, "red")
                crossroad.ChangeTrafficLightColor(72, "green")
                crossroad.ChangeTrafficLightColor(119, "green")
                crossroad.ChangeTrafficLightColor(168, "red")
                crossroad.ChangeTrafficLightColor(215, "red")
                crossroad.ChangeTrafficLightColor(263, "green")
                # Crossroad 2
                crossroad.ChangeTrafficLightColor(23+ppa, "red")
                crossroad.ChangeTrafficLightColor(72+ppa, "green")
                crossroad.ChangeTrafficLightColor(119+ppa, "green")
                crossroad.ChangeTrafficLightColor(168+ppa, "red")
                crossroad.ChangeTrafficLightColor(215+ppa, "red")
                crossroad.ChangeTrafficLightColor(264+ppa, "green")
                crossroad.ChangeTrafficLightColor(311+ppa, "green")
                crossroad.ChangeTrafficLightColor(360+ppa, "red")
                # Crossroad 3
                crossroad.ChangeTrafficLightColor(167+ppa2, "green")
                crossroad.ChangeTrafficLightColor(120+ppa2, "green")
                crossroad.ChangeTrafficLightColor(71+ppa2, "red")
                crossroad.ChangeTrafficLightColor(24+ppa2, "red")
                crossroad.ChangeTrafficLightColor(263+ppa2, "green")
                crossroad.ChangeTrafficLightColor(216+ppa2, "green")

                ok = False
            else:
                # Crossroad 1
                crossroad.ChangeTrafficLightColor(23, "green")
                crossroad.ChangeTrafficLightColor(72, "red")
                crossroad.ChangeTrafficLightColor(119, "red")
                crossroad.ChangeTrafficLightColor(168, "green")
                crossroad.ChangeTrafficLightColor(215, "green")
                crossroad.ChangeTrafficLightColor(263, "red")
                # Crossroad 2
                crossroad.ChangeTrafficLightColor(23+ppa, "green")
                crossroad.ChangeTrafficLightColor(72+ppa, "red")
                crossroad.ChangeTrafficLightColor(119+ppa, "red")
                crossroad.ChangeTrafficLightColor(168+ppa, "green")
                crossroad.ChangeTrafficLightColor(215+ppa, "green")
                crossroad.ChangeTrafficLightColor(264+ppa, "red")
                crossroad.ChangeTrafficLightColor(311+ppa, "red")
                crossroad.ChangeTrafficLightColor(360+ppa, "green")
                # Crossroad 3
                crossroad.ChangeTrafficLightColor(167+ppa2, "red")
                crossroad.ChangeTrafficLightColor(120+ppa2, "red")
                crossroad.ChangeTrafficLightColor(71+ppa2, "green")
                crossroad.ChangeTrafficLightColor(24+ppa2, "green")
                crossroad.ChangeTrafficLightColor(263+ppa2, "red")
                crossroad.ChangeTrafficLightColor(216+ppa2, "red")

                ok = True
    

my_thread = threading.Thread(target=restapi, args=())
my_thread.start()

# Spawn new cars thread
def SpawnNewCars():
    while True:
        time.sleep(0.01)
        if len(crossroad.cars) < CAR_AMOUNT:
            best_way = random.choice(best_ways)
            start = best_way[0]
            finish = best_way[len(best_way)-1]
            AddCar((random.randint(0, 255), random.randint(0, 255), random.randint(0, 255)), start, finish, 15, 2, best_way)

spawn_new_cars = threading.Thread(target=SpawnNewCars, args=())
spawn_new_cars.start()

print("Loop has been started.")
while True:
    crossroad.CarsMovement()

    address_led_strip.DisplayPixels(crossroad.crossroad_road)

    # a = input()
    time.sleep(0.03)
