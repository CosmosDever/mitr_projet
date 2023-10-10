#AIzaSyCdQOUa3vVKSG_hA4RVmSD7O0d39TSOy9g

import googlemaps
import csv

api_key = 'AIzaSyCdQOUa3vVKSG_hA4RVmSD7O0d39TSOy9g'

gmaps = googlemaps.Client(key=api_key)

class Plot:
    def __init__(self, plot_id, field, ccs, crop_date, plot_location, farmer):
        self.plot_id = plot_id
        self.field = field
        self.ccs = ccs
        self.crop_date = crop_date
        self.plot_location = plot_location
        self.farmer = farmer
        self.routes = {}
        self.contractor_name = None
        self.truck_id = None
        self.distance_to_each_harvest_cars = {} 
        self.distances_to_factories = {}  

    def calculate_distance(self, harvest_car):
        route = gmaps.directions(
            self.plot_location,
            harvest_car.car_location,
            mode="driving",
            units="metric"
        )

        if route:
            distance = float(route[0]["legs"][0]["distance"]["text"].split()[0]) 
            self.truck_id = harvest_car.car_id  
            if harvest_car.car_id in self.distance_to_each_harvest_cars:
                self.distance_to_each_harvest_cars[harvest_car.car_id] += distance  
            else:
                self.distance_to_each_harvest_cars[harvest_car.car_id] = distance
            return distance
        else:
            return 0.0

    def calculate_distance_to_factory(self, factory):
        route = gmaps.directions(
            self.plot_location,
            factory['location'],
            mode="driving",
            units="metric"
        )

        if route:
            distance = float(route[0]["legs"][0]["distance"]["text"].split()[0])  # Extract numerical distance
            self.distances_to_factories[factory['name']] = distance  # Store distance in the dictionary

class HarvestCar:
    def __init__(self, car_id, car_location, contractor, status):
        self.car_id = car_id
        self.car_location = car_location
        self.contractor = contractor
        self.status = status

    def calculate_distance(self, plot_location):
        route = gmaps.directions(
            plot_location,
            self.car_location,
            mode="driving",
            units="metric"
        )

        if route:
            distance = float(route[0]["legs"][0]["distance"]["text"])
            return distance
        else:
            return "N/A"

class Contractor:
    def __init__(self, name, num_harvest_car, harvest_car_location, harvest_cap, num_all_truck, all_truck_cap):
        self.name = name
        self.num_harvest_car = num_harvest_car
        self.harvest_car_location = harvest_car_location
        self.harvest_cap = harvest_cap
        self.num_all_truck = num_all_truck
        self.all_truck_cap = all_truck_cap

class Truck:
    def __init__(self, truck_id, truck_type, num_truck, truck_cap, contractor):
        self.truck_id = truck_id
        self.truck_type = truck_type
        self.num_truck = num_truck
        self.truck_cap = truck_cap
        self.contractor = contractor

# Read Contractor 
contractors = []
with open('SugarcaneData - Contractor.csv', mode='r', encoding='utf-8') as file:
    reader = csv.DictReader(file)
    for row in reader:
        contractor = Contractor(
            row['Contractor'],
            int(row['NumHarvestCar']),
            row['HarvestCarLoc'],
            float(row['HarvestCap']),
            int(row['NumAllTruck']),
            float(row['AllTruckCap'])
        )
        contractors.append(contractor)

# Read Truck 
trucks = []
with open('SugarcaneData - TruckType.csv', mode='r', encoding='utf-8') as file:
    reader = csv.DictReader(file)
    for row in reader:
        truck = Truck(
            row['TruckID'],
            row['TruckType'],
            int(row['NumTruck']),
            float(row['TruckCap']),
            row['Contractor']
        )
        trucks.append(truck)

# Read plot data
plots = []
with open('SugarcaneData - Plot.csv', mode='r', encoding='utf-8') as file:
    reader = csv.DictReader(file)
    for row in reader:
        plot = Plot(
            row['PlotID'],
            int(row['Field']),
            float(row['CCS']),
            row['CropDate'],
            row['PlotLoc'],
            row['Farmer']
        )
        plots.append(plot)

# Define the list of harvest cars
harvest_cars = []

# Read CSV file containing harvest car data
with open('SugarcaneData - HarvestCar.csv', mode='r', encoding='utf-8') as file:
    reader = csv.DictReader(file)
    for row in reader:
        car = HarvestCar(
            row['HarvestCar'],
            row['HarvestCarLoc'],
            row['Contractor'],
            int(row['Status'])
        )
        if car.status == 1:  # Only consider harvest cars with Status = 1
            harvest_cars.append(car)

# Read Factory data
factories = []
with open('SugarcaneData - Factory.csv', mode='r', encoding='utf-8') as file:
    reader = csv.DictReader(file)
    for row in reader:
        factory = {
            'name': row['Factory'],
            'location': row['FactoryLoc']
        }
        factories.append(factory)

# Calculate distances for harvest cars and plots
for harvest_car in [car for car in harvest_cars if car.status == 1]:
    for plot in plots:
        distance = plot.calculate_distance(harvest_car)
        plot.routes[harvest_car.car_id] = distance

# Calculate distances for plots and factories
for plot in plots:
    for factory in factories:
        plot.calculate_distance_to_factory(factory)
        
# Create a dictionary to map HarvestCar IDs to contractor names and TruckIDs        
harvest_car_info = {}
for harvest_car in harvest_cars:
    harvest_car_info[harvest_car.car_id] = {
        'contractor_name': harvest_car.contractor,
        'truck_id': None  # Initialize TruckID as None
    }
    
# Sort the plots by distance to the nearest harvest car
for plot in plots:
    nearest_harvest_car_id = min(plot.routes.items(), key=lambda x: float(x[1]))[0]
    plot.nearest_harvest_car = nearest_harvest_car_id
    plot.distance_to_nearest = plot.routes[nearest_harvest_car_id]
    # Populate contractor name and TruckID based on the nearest harvest car
    plot.contractor_name = harvest_car_info[nearest_harvest_car_id]['contractor_name']
    plot.truck_id = harvest_car_info[nearest_harvest_car_id]['truck_id']

# Write the updated plot and harvest car data back to CSV files
with open('SugarcaneData - Plot_with_distances.csv', mode='w', newline='', encoding='utf-8') as file:
    fieldnames = ['PlotID', 'Field', 'CCS', 'CropDate', 'PlotLoc', 'Farmer', 'distance_to_nearest', 'nearest_harvest_car', 'contractor_name', 'truck_id', 'distance_to_each_harvest_cars', 'distances_to_factories']
    writer = csv.DictWriter(file, fieldnames=fieldnames)
    writer.writeheader()
    for plot in plots:
        writer.writerow({
            'PlotID': plot.plot_id,
            'Field': plot.field,
            'CCS': plot.ccs,
            'CropDate': plot.crop_date,
            'PlotLoc': plot.plot_location,
            'Farmer': plot.farmer,
            'distance_to_nearest': plot.distance_to_nearest,
            'nearest_harvest_car': plot.nearest_harvest_car,
            'contractor_name': plot.contractor_name,
            'truck_id': plot.truck_id,
            'distance_to_each_harvest_cars': plot.distance_to_each_harvest_cars,
            'distances_to_factories': plot.distances_to_factories
        })

