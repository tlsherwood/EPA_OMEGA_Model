"""
__init.py__
===========

"""

import pandas as pd
pd.set_option('chained_assignment', 'raise')

from omega_db import *
import file_eye_oh as fileio
from input_validation import *

import matplotlib.pyplot as plt

# from copy import copy, deepcopy
# import numpy as np
# import networkx as nx
# import itertools
# import cProfile
# import time

# --- OMEGA2 globals ---

# enumerated values
fueling_classes = ['BEV', 'ICE']
hauling_classes = ['hauling', 'non hauling']
ownership_classes = ['shared', 'private']
reg_classes = ['car', 'truck']
fuel_units = ['gallon', 'kWh']

# OMEGA2 code version number
code_version = "phase0.0.0"
# OMEGA2 input file format version number
input_format_version = '0.0'

print('loading usepa_omega2 version %s' % code_version)


class OMEGA2RuntimeOptions(object):
    def __init__(self):
        self.verbose = True
        self.output_folder = 'output/'
        self.database_dump_folder = '__dump'
        self.fuels_file = 'input_templates/fuels.csv'
        self.manufacturers_file = 'input_templates/manufacturers.csv'
        self.market_classes_file = 'input_templates/market_classes.csv'
        self.vehicles_file = 'input_templates/vehicles.csv'
        self.showroom_data_file = 'input_templates/showroom_data.csv'
        self.ghg_standards_file = 'input_templates/ghg_standards-flat.csv'  # or ghg_standards-footprint.csv
        self.fuel_scenarios_file = 'input_templates/fuel_scenarios.csv'
        self.fuel_scenario_annual_data_file = 'input_templates/fuel_scenario_annual_data.csv'
        self.cost_curves_file = 'input_templates/cost_curves_TEMP.csv'
        self.cost_clouds_file = 'input_templates/cost_clouds.csv'


o2_options = OMEGA2RuntimeOptions()
