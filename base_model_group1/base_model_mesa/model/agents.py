# Importing necessary libraries
import random
from mesa import Agent
from shapely.geometry import Point
from shapely import contains_xy

# Import functions from functions.py
from functions import generate_random_location_within_map_domain, get_flood_depth, calculate_basic_flood_damage, floodplain_multipolygon


# Define the Households agent class
class Households(Agent):
    """
    An agent representing a household in the model.
    Each household has a flood depth attribute which is randomly assigned for demonstration purposes.
    In a real scenario, this would be based on actual geographical data or more complex logic.
    """

    def __init__(self, unique_id, model, worry=None):
        super().__init__(unique_id, model)
        self.is_adapted = False  # Initial adaptation status set to False
        #parameter
        self.cost = 1
        self.response_efficacy =1
        self.self_efficacy = 1
        self.government_policy =1

        self.income =  random.gauss(50000, 20000)
        self.age =  random.gauss(40, 10)

        # getting flood map values
        # Get a random location on the map
        
        #
        
        loc_x, loc_y = generate_random_location_within_map_domain()
        self.location = Point(loc_x, loc_y)
        
        #List to store adaptiation and timesteps 
 
        self.adaptation_action = 0; 


        if worry is None: 
            self.worry = random.betavariate(0.3,0.7)
        else: 
            self.worry = worry 
        
        #define neighbours: 
        self.neighbours = []
        self.avg_investment_neighbour =0 
        self.investment = 0 


        # Check whether the location is within floodplain
        self.in_floodplain = False
        if contains_xy(geom=floodplain_multipolygon, x=self.location.x, y=self.location.y):
            self.in_floodplain = True

        # Get the estimated flood depth at those coordinates. 
        # the estimated flood depth is calculated based on the flood map (i.e., past data) so this is not the actual flood depth
        # Flood depth can be negative if the location is at a high elevation
        self.flood_depth_estimated = get_flood_depth(corresponding_map=model.flood_map, location=self.location, band=model.band_flood_img)
        # handle negative values of flood depth
        if self.flood_depth_estimated < 0:
            self.flood_depth_estimated = 0
        
        # calculate the estimated flood damage given the estimated flood depth. Flood damage is a factor between 0 and 1
        self.flood_damage_estimated = calculate_basic_flood_damage(flood_depth=self.flood_depth_estimated)

        # Add an attribute for the actual flood depth. This is set to zero at the beginning of the simulation since there is not flood yet
        # and will update its value when there is a shock (i.e., actual flood). Shock happens at some point during the simulation
        self.flood_depth_actual = 0
        
        #calculate the actual flood damage given the actual flood depth. Flood damage is a factor between 0 and 1
        self.flood_damage_actual = calculate_basic_flood_damage(flood_depth=self.flood_depth_actual)
    
    def update_self_investment (self, c):
        self.investment += c
    
    def compute_threat_appraisal(self, flood_damage_estimated, perceived_flood_probability):
        threat_appraisal = self.worry + flood_damage_estimated + perceived_flood_probability
        return threat_appraisal

    def compute_coping_appraisal(self, cost, response_efficacy, self_efficacy, government_policy):
        coping_appraisal = (response_efficacy + self_efficacy - cost) * government_policy
        return coping_appraisal

    def compute_w2p(self, threat_appraisal, coping_appraisal):
        w2p = threat_appraisal + coping_appraisal
        return w2p
    
    #first the agent has to decide on whether it will take action or not
    def decide_action(self, income, age, w2p):
        #w2p = self.compute_w2p(self.compute_threat_appraisal(), self.compute_coping_appraisal())
        if w2p > 0.5:
            self.action(income, age)
        else:
            self.worry *= 0.05

    #then if it takes action it has to decide on which action it will take
    def action(self, income, age):
        I = 50000  # Some income threshold
        A = 50  # Some age threshold
        if income > I:
            if age < A:
                self.flood_barrier()
            else:
                self.structural_measures()
        else:
            if age < A:
                self.adaptive_building_use()
            else:
                self.flood_insurance()

    def flood_barrier(self):
        # Assuming flood_damage_actual is a property of the household
        self.flood_damage_actual *= 0.2
        self.worry *= 0.2
        self.update_self_investment(0.8) 
        #self.record_action('flood_barrier')  # Record the action
        self.adaptation_action = 1

    def structural_measures(self):
        self.flood_damage_actual *= 0.4
        self.worry *= 0.4
        self.update_self_investment(0.6)
        #self.record_action('structural_measures')
        self.adaptation_action = 2

    def adaptive_building_use(self):
        self.flood_damage_actual *= 0.6
        self.worry *= 0.6
        self.update_self_investment(0.4)
        #self.record_action('adaptive_building_use')  # Record the action
        self.adaptation_action = 3


    def flood_insurance(self):
        self.flood_damage_actual *= 0.8
        self.worry *= 0.8
        self.update_self_investment(0.2)
        #self.record_action('flood_insurance')  # Record the action
        self.adaptation_action = 4

    def record_action(self, action_name):
        self.adaptation_actions.append(action_name)


    # Function to count friends who can be influencial.
    def count_friends(self, radius):
        """Count the number of neighbors within a given radius (number of edges away). This is social relation and not spatial"""
        friends = self.model.grid.get_neighborhood(self.pos, include_center=False, radius=radius)
        return len(friends)

    def step(self):
        
        threat_appraisal = self.compute_threat_appraisal(flood_damage_estimated=self.flood_damage_estimated, perceived_flood_probability=1)

        coping_appraisal = self.compute_coping_appraisal(cost=self.cost, response_efficacy=self.response_efficacy, self_efficacy=self.self_efficacy, government_policy = self.government_policy)
        w2p = self.compute_w2p(threat_appraisal, coping_appraisal)
        self.decide_action(income=self.income, age=self.age, w2p=w2p)
        
        # Logic for adaptation based on estimated flood damage and a random chance.
        # These conditions are examples and should be refined for real-world applications.
        if self.flood_damage_estimated > 0.15 and random.random() < 0.2:
            self.is_adapted = True  # Agent adapts to flooding
        
# Define the Government agent class
class Government(Agent):
    """
    A government agent that currently doesn't perform any actions.
    """
    def __init__(self, unique_id, model):
        super().__init__(unique_id, model)

    def step(self):
        # The government agent doesn't perform any actions.
        pass

# More agent classes can be added here, e.g. for insurance agents.