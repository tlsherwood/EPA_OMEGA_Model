"""
__init.py__
===========


"""

import enum
import pandas as pd
pd.set_option('chained_assignment', 'raise')

from omega_db import *
from omega_types import *
import omega_log
import file_eye_oh as fileio
from input_validation import *

import matplotlib.pyplot as plt
import scipy.interpolate

import os

# from copy import copy, deepcopy
# import numpy as np
# import networkx as nx
# import itertools
# import cProfile
# import time

# --- OMEGA2 globals ---

# enumerated values
fueling_classes = OmegaEnum(['BEV', 'ICE'])
hauling_classes = OmegaEnum(['hauling', 'non hauling'])
ownership_classes = OmegaEnum(['shared', 'private'])
reg_classes = OmegaEnum(['car', 'truck'])
fuel_units = OmegaEnum(['gallon', 'kWh'])

# OMEGA2 code version number
code_version = "phase0.1"

print('loading usepa_omega2 version %s' % code_version)

class OMEGA2RuntimeOptions(object):
    def __init__(self):
        self.verbose = False
        self.output_folder = 'output/'
        self.database_dump_folder = '__dump'
        self.fuels_file = 'input_templates/fuels.csv'
        self.manufacturers_file = 'input_templates/manufacturers.csv'
        self.market_classes_file = 'input_templates/market_classes.csv'
        self.vehicles_file = 'input_templates/vehicles.csv'
        self.demanded_sales_annual_data_file = 'input_templates/demanded_sales_annual_data.csv'
        self.fuel_scenarios_file = 'input_templates/fuel_scenarios.csv'
        self.fuel_scenario_annual_data_file = 'input_templates/fuel_scenario_annual_data.csv'
        self.cost_curves_file = 'input_templates/cost_curves.csv'
        self.cost_clouds_file = 'input_templates/cost_clouds.csv'
        self.cost_curve_frontier_affinity_factor = 0.75
        self.analysis_initial_year = None
        self.analysis_final_year = None
        self.logfile_prefix = self.output_folder + os.sep + 'o2log_'
        self.logfilename = ''
        self.producer_calculate_generalized_cost = None
        self.consumer_calculate_generalized_cost = None
        self.GHG_standard = 'footprint'
        if self.GHG_standard == 'flat':
            self.ghg_standards_file = 'input_templates/ghg_standards-flat.csv'
        else:
            self.ghg_standards_file = 'input_templates/ghg_standards-footprint.csv'
        self.stock_scrappage = 'fixed'
        self.stock_vmt = 'fixed'
        if self.stock_scrappage == 'fixed':
            self.reregistration_fixed_by_age_file = 'input_templates/reregistration_fixed_by_age.csv'
        else:
            pass
        if self.stock_vmt == 'fixed':
            self.annual_vmt_fixed_by_age_file = 'input_templates/annual_vmt_fixed_by_age.csv'
        else:
            pass
        self.slice_tech_combo_cloud_tables = True
        self.allow_backsliding = False


o2_options = OMEGA2RuntimeOptions()

omega_log.init_logfile(o2_options)
