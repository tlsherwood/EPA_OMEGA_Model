"""

Functions to get vehicle data based on vehicle ID, vehicle emission factors for the given vehicle model year and reg-class, refinery and power section emission factors for the given calendar year,
and then to calculate from them the pollutant inventories, including fuel consumed, for each year in the analysis.



----

**CODE**

"""
import pandas as pd

from omega_model import *


def get_vehicle_emission_rate(model_year, sourcetype_name, reg_class_id, fuel, ind_var_value): #, *rate_names):
    """

    Args:
        model_year: The model year of the specific vehicle.
        sourcetype_name: The MOVES sourcetype name (e.g., 'passenger car', 'light commercial truck')
        reg_class_id: The regulatory class ID of the vehicle.
        fuel: The fuel ID (i.e., pump gasoline, pump diesel)
        ind_var_value: The independent variable value

    Returns:
        A list of emission factors as specified in the emission_factors list for the given model-year vehicle in a given calendar year.

    """
    from effects.emission_rates_vehicles import EmissionRatesVehicles

    if 'gasoline' in fuel:
        rate_names = [
            'pm25_brakewear_grams_per_mile',
            'pm25_tirewear_grams_per_mile',
            'pm25_exhaust_grams_per_mile',
            'nmog_exhaust_grams_per_mile',
            'nmog_evap_permeation_grams_per_gallon',
            'nmog_evap_fuel_vapor_venting_grams_per_gallon',
            'nmog_evap_fuel_leaks_grams_per_gallon',
            'nmog_refueling_displacement_grams_per_gallon',
            'nmog_refueling_spillage_grams_per_gallon',
            'co_exhaust_grams_per_mile',
            'nox_exhaust_grams_per_mile',
            'sox_exhaust_grams_per_gallon',
            # 'benzene_exhaust_grams_per_mile',
            # 'butadiene13_exhaust_grams_per_mile',
            # 'formaldehyde_exhaust_grams_per_mile',
            # 'acetaldehyde_exhaust_grams_per_mile',
            # 'acrolein_exhaust_grams_per_mile',
            'ch4_exhaust_grams_per_mile',
            'n2o_exhaust_grams_per_mile',
        ]
    elif 'diesel' in fuel:
        rate_names = [
            'pm25_brakewear_grams_per_mile',
            'pm25_tirewear_grams_per_mile',
            'pm25_exhaust_grams_per_mile',
            'nmog_exhaust_grams_per_mile',
            'nmog_refueling_spillage_grams_per_gallon',
            'co_exhaust_grams_per_mile',
            'nox_exhaust_grams_per_mile',
            'sox_exhaust_grams_per_gallon',
            'ch4_exhaust_grams_per_mile',
            'n2o_exhaust_grams_per_mile',
        ]
    elif 'electric' in fuel:
        rate_names = [
            'pm25_brakewear_grams_per_mile',
            'pm25_tirewear_grams_per_mile'
        ]
    else:
        rate_names = []

    rates = EmissionRatesVehicles.get_emission_rate(model_year, sourcetype_name, reg_class_id, fuel,
                                                    ind_var_value, *rate_names)

    return rates


def get_egu_emission_rate(calendar_year, kwh_consumption, kwh_generation):
    """

    Args:
        calendar_year: The calendar year for which power sector emission factors are needed.
        kwh_consumption: The energy consumed by the vehicle, measured at the wall or charger outlet
        kwh_generation: The energy generated to satisfy the kwh_consumption value (not used)

    Returns:
        A list of power sector emission factors as specified in the emission_factors list for the given calendar year.

    """
    from effects.emission_rates_egu import EmissionRatesEGU

    kwh_session = kwh_consumption

    rate_names = ('co_grams_per_kwh',
                  'nox_grams_per_kwh',
                  'pm25_grams_per_kwh',
                  'sox_grams_per_kwh',
                  'co2_grams_per_kwh',
                  'ch4_grams_per_kwh',
                  'n2o_grams_per_kwh',
                  )

    return EmissionRatesEGU.get_emission_rate(calendar_year, kwh_session, rate_names)


def get_refinery_ef(calendar_year, fuel):
    """

    Args:
        calendar_year: The calendar year for which a refinery emission factors are needed.
        fuel: The fuel ID for which refinery emission factors are needed (i.e., pump_gasoline, pump_diesel).

    Returns:
        A list of refinery emission factors as specified in the emission_factors list for the given calendar year and liquid fuel.

    """
    from effects.emission_factors_refinery import EmissionFactorsRefinery

    emission_factors = (
        'voc_grams_per_gallon',
        'co_grams_per_gallon',
        'nox_grams_per_gallon',
        'pm25_grams_per_gallon',
        'sox_grams_per_gallon',
        # 'benzene_grams_per_gallon',
        # 'butadiene13_grams_per_gallon',
        # 'formaldehyde_grams_per_gallon',
        # 'acetaldehyde_grams_per_gallon',
        # 'acrolein_grams_per_gallon',
        'co2_grams_per_gallon',
        'ch4_grams_per_gallon',
        'n2o_grams_per_gallon',
    )

    return EmissionFactorsRefinery.get_emission_factors(calendar_year, fuel, emission_factors)


def get_energysecurity_cf(calendar_year):
    """
    Get energy security cost factors

    Args:
        calendar_year: The calendar year for which energy security related factors are needed.

    Returns:
        A list of cost factors as specified in the cost_factors list for the given calendar year.

    """
    from effects.cost_factors_energysecurity import CostFactorsEnergySecurity

    cost_factors = ('oil_import_reduction_as_percent_of_total_oil_demand_reduction',
                    )

    return CostFactorsEnergySecurity.get_cost_factors(calendar_year, cost_factors)


def get_inputs_for_effects(arg=None):

    """
    Get general inputs needed for effects calculations.

    Args:
        arg: The attribute for which an attribute value is needed.

    Returns:
        A list of necessary input values; use index=[0] if passing a single attribute.

    """
    from effects.general_inputs_for_effects import GeneralInputsForEffects

    if arg:
        return GeneralInputsForEffects.get_value(arg)
    else:
        args = [
            'grams_per_us_ton',
            'grams_per_metric_ton',
            'gal_per_bbl',
            'e0_in_retail_gasoline',
            'e0_energy_density_ratio',
            # 'gallons_of_gasoline_us_annual',
            # 'bbl_oil_us_annual',
            # 'kwh_us_annual',
            # 'year_for_compares',
        ]
        values = list()
        for arg in args:
            values.append(GeneralInputsForEffects.get_value(arg))

        return values


def calc_physical_effects(calendar_years, safety_effects_dict): #, adjusted_vmt):
    """

    Args:
        calendar_years: The years for which emission inventories and fuel consumptions will be calculated.
        safety_effects_dict: The dictionary generated via the safety_effects module.
        adjusted_vmt: object; an object of the AdjustmentsVMT class.

    Returns:
        A dictionary key, value pair where the key is a tuple (vehicle_id, calendar_year, age) and the value is a dictionary of key, value pairs providing
        vehicle attributes (e.g., model_year, reg_class_id, in_use_fuel_id, etc.) and inventory attributes (e.g., co2 tons, fuel consumed, etc.) and their attribute values.

    """
    from producer.vehicle_annual_data import VehicleAnnualData
    from producer.vehicles import VehicleFinal
    from context.onroad_fuels import OnroadFuel
    from common.omega_eval import Eval

    vehicle_attribute_list = [
        'manufacturer_id',
        'name',
        'model_year',
        'base_year_reg_class_id',
        'reg_class_id',
        'in_use_fuel_id',
        'market_class_id',
        'fueling_class',
        'base_year_powertrain_type',
        'target_co2e_grams_per_mile',
        'onroad_direct_co2e_grams_per_mile',
        'onroad_direct_kwh_per_mile',
        'body_style',
        'base_year_curbweight_lbs',
        'curbweight_lbs',
    ]

    grams_per_us_ton, grams_per_metric_ton, gal_per_bbl, e0_share, e0_energy_density_ratio = get_inputs_for_effects()
    # gallons_of_gasoline_us_annual, bbl_oil_us_annual, kwh_us_annual, year_for_compares = get_inputs_for_effects(*input_attributes_list)

    # year_for_compares = int(year_for_compares)

    physical_effects_dict = dict()
    vehicle_info_dict = dict()
    for calendar_year in calendar_years:

        vads = VehicleAnnualData.get_vehicle_annual_data(calendar_year)

        # UPDATE physical effects data
        calendar_year_effects_dict = dict()

        # first a loop to determine kwh demand for this calendar year
        fuel_consumption_kWh_annual = fuel_generation_kWh_annual = 0
        for vad in vads:

            # need vehicle info once for each vehicle, not every calendar year for each vehicle
            vehicle_id = int(vad['vehicle_id'])
            age = int(vad['age'])

            if vehicle_id not in vehicle_info_dict:
                vehicle_info_dict[vehicle_id] \
                    = VehicleFinal.get_vehicle_attributes(vehicle_id, vehicle_attribute_list)

            mfr_id, name, model_year, base_year_reg_class_id, reg_class_id, in_use_fuel_id, market_class_id, fueling_class, \
            base_year_powertrain_type, target_co2e_grams_per_mile, onroad_direct_co2e_grams_per_mile, \
            onroad_direct_kwh_per_mile, body_style, base_year_curbweight_lbs, curbweight_lbs \
                = vehicle_info_dict[vehicle_id]

            fuel_dict = Eval.eval(in_use_fuel_id, {'__builtins__': None}, {})
            for fuel, fuel_share in fuel_dict.items():
                if fuel == 'US electricity' and onroad_direct_kwh_per_mile:
                    # refuel_efficiency = OnroadFuel.get_fuel_attribute(calendar_year, fuel, 'refuel_efficiency')
                    transmission_efficiency = OnroadFuel.get_fuel_attribute(calendar_year, fuel, 'transmission_efficiency')

                    safety_effects_key = (vehicle_id, calendar_year, age)
                    vmt = safety_effects_dict[safety_effects_key]['vmt']
                    vmt_electricity = vmt * fuel_share
                    fuel_consumption_kWh_annual += vmt_electricity * onroad_direct_kwh_per_mile
                    fuel_generation_kWh_annual = fuel_consumption_kWh_annual / transmission_efficiency

        # upstream EGU emission rates for electric fuel operation
        co_egu, nox_egu, pm25_egu, sox_egu, co2_egu, ch4_egu, n2o_egu \
            = get_egu_emission_rate(calendar_year, fuel_consumption_kWh_annual, fuel_generation_kWh_annual)

        for vad in vads:

            vehicle_id = int(vad['vehicle_id'])
            age = int(vad['age'])

            mfr_id, name, model_year, base_year_reg_class_id, reg_class_id, in_use_fuel_id, market_class_id, fueling_class, \
            base_year_powertrain_type, target_co2e_grams_per_mile, onroad_direct_co2e_grams_per_mile, \
            onroad_direct_kwh_per_mile, body_style, base_year_curbweight_lbs, curbweight_lbs \
                = vehicle_info_dict[vehicle_id]

            if model_year >= calendar_years[0]:

                # get vmt and session fatalities from safety_effects_dict
                safety_effects_key = (vehicle_id, calendar_year, age)
                session_fatalities \
                    = safety_effects_dict[safety_effects_key]['session_fatalities']
                vmt = safety_effects_dict[safety_effects_key]['vmt']
                annual_vmt = safety_effects_dict[safety_effects_key]['annual_vmt']
                odometer = safety_effects_dict[safety_effects_key]['odometer']
                calendar_year_vmt_adj = safety_effects_dict[safety_effects_key]['vmt_adjustment']

                sourcetype_name = 'passenger car' # TODO does this come from somewhere at some point?
                if base_year_reg_class_id == 'truck':
                    sourcetype_name = 'passenger truck'

                # need vehicle effects for each vehicle and for each calendar year since they change year-over-year
                vehicle_effects_dict = dict()
                flag = None
                if target_co2e_grams_per_mile is not None:

                    liquid_fuel = None
                    electric_fuel = None

                    vmt_liquid_fuel = vmt_electricity \
                        = onroad_gallons_per_mile = fuel_consumption_gallons \
                        = fuel_generation_kWh = fuel_consumption_kWh = 0

                    nmog_tailpipe_ustons = nmog_evap_ustons = nmog_vehicle_ustons = 0
                    co_vehicle_ustons = nox_vehicle_ustons = sox_vehicle_ustons = 0
                    pm25_tailpipe_ustons = pm25_brakewear_ustons = pm25_tirewear_ustons = pm25_vehicle_ustons = 0
                        # benzene_tailpipe_ustons = butadiene13_tailpipe_ustons = formaldehyde_tailpipe_ustons \
                    #     = acetaldehyde_tailpipe_ustons = acrolein_tailpipe_ustons = 0

                    ch4_vehicle_metrictons = n2o_vehicle_metrictons = co2_vehicle_metrictons = 0

                    pm25_brakewear_l = pm25_brakewear_e = pm25_tirewear_l = pm25_tirewear_e = 0
                    pm25_exhaust = nmog = co = nox = sox = ch4 = n2o = 0
                    nmog_permeation = nmog_venting = nmog_leaks = nmog_refuel_disp = nmog_refuel_spill = 0

                    # co_egu = nox_egu = pm25_egu = sox_egu = co2_egu = ch4_egu = n2o_egu = 0
                    voc_ref = co_ref = nox_ref = pm25_ref = sox_ref = co2_ref = ch4_ref = n2o_ref = 0
                    # benzene_ref = butadiene13_ref = formaldehyde_ref = acetaldehyde_ref = acrolein_ref = 0

                    veh_rates_by = 'age'  # for now; set as an input if we want to; value can be 'age' or 'odometer'
                    ind_var_value = pd.to_numeric(vad['age'])
                    if veh_rates_by == 'odometer':
                        ind_var_value = pd.to_numeric(vad['odometer'])

                    fuel_dict = Eval.eval(in_use_fuel_id, {'__builtins__': None}, {})
                    for fuel, fuel_share in fuel_dict.items():
                        refuel_efficiency = OnroadFuel.get_fuel_attribute(calendar_year, fuel, 'refuel_efficiency')
                        transmission_efficiency = OnroadFuel.get_fuel_attribute(calendar_year, fuel, 'transmission_efficiency')
                        co2_emissions_grams_per_unit = OnroadFuel.get_fuel_attribute(calendar_year, fuel, 'direct_co2e_grams_per_unit') / refuel_efficiency

                        # calc fuel consumption and get emission rates
                        if fuel == 'US electricity' and onroad_direct_kwh_per_mile:
                            electric_fuel = fuel
                            vmt_electricity = vmt * fuel_share
                            fuel_consumption_kWh += vmt_electricity * onroad_direct_kwh_per_mile
                            fuel_generation_kWh = fuel_consumption_kWh / transmission_efficiency

                            # vehicle emission rates; PHEVs use the ICE vehicle rates
                            if fueling_class == 'BEV':
                                pm25_brakewear_e, pm25_tirewear_e \
                                    = get_vehicle_emission_rate(model_year, sourcetype_name, base_year_reg_class_id, fuel,
                                                                ind_var_value) #, *bev_veh_rate_names)
                            #
                            # # upstream EGU emission factors for electric fuel operation
                            # co_egu, nox_egu, pm25_egu, sox_egu, co2_egu, ch4_egu, n2o_egu \
                            #     = get_egu_emission_rate(calendar_year, fuel_generation_kWh)

                        elif fuel != 'US electricity' and onroad_direct_co2e_grams_per_mile:
                            liquid_fuel = fuel
                            vmt_liquid_fuel = vmt * fuel_share
                            onroad_gallons_per_mile += onroad_direct_co2e_grams_per_mile / co2_emissions_grams_per_unit
                            fuel_consumption_gallons = vmt_liquid_fuel * onroad_gallons_per_mile / transmission_efficiency

                            if fuel == 'pump gasoline':
                                pm25_brakewear_l, pm25_tirewear_l, pm25_exhaust, \
                                nmog, nmog_permeation, nmog_venting, nmog_leaks, nmog_refuel_disp, nmog_refuel_spill, \
                                co, nox, sox, ch4, n2o \
                                    = get_vehicle_emission_rate(model_year, sourcetype_name, base_year_reg_class_id, fuel,
                                                                ind_var_value)

                            elif fuel == 'pump diesel':
                                pm25_brakewear_l, pm25_tirewear_l, pm25_exhaust, \
                                nmog, nmog_refuel_spill, \
                                co, nox, sox, ch4, n2o \
                                    = get_vehicle_emission_rate(model_year, sourcetype_name, base_year_reg_class_id, fuel,
                                                                ind_var_value)
                            else:
                                pass # add additional liquid fuels (E85) if necessary

                            # upstream refinery emission factors for liquid fuel operation
                            # voc_ref, co_ref, nox_ref, pm25_ref, sox_ref, benzene_ref, butadiene13_ref, formaldehyde_ref, \
                            # acetaldehyde_ref, acrolein_ref, co2_ref, ch4_ref, n2o_ref \
                            #     = get_refinery_ef(calendar_year, liquid_fuel)
                            voc_ref, co_ref, nox_ref, pm25_ref, sox_ref, co2_ref, ch4_ref, n2o_ref \
                                = get_refinery_ef(calendar_year, liquid_fuel)

                            # calc tailpipe emissions for liquid fuel operation
                            factor = vmt_liquid_fuel / grams_per_us_ton
                            nmog_tailpipe_ustons += nmog * factor
                            co_vehicle_ustons += co * factor
                            nox_vehicle_ustons += nox * factor
                            pm25_tailpipe_ustons += pm25_exhaust * factor
                            # benzene_tailpipe_ustons += benzene * factor
                            # butadiene13_tailpipe_ustons += butadiene13 * factor
                            # formaldehyde_tailpipe_ustons += formaldehyde * factor
                            # acetaldehyde_tailpipe_ustons += acetaldehyde * factor
                            # acrolein_tailpipe_ustons += acrolein * factor

                            factor = fuel_consumption_gallons / grams_per_us_ton
                            sox_vehicle_ustons += sox * factor
                            nmog_evap_ustons += sum([nmog_permeation,
                                                     nmog_venting,
                                                     nmog_leaks,
                                                     nmog_refuel_disp,
                                                     nmog_refuel_spill]) * factor

                            nmog_vehicle_ustons = nmog_tailpipe_ustons + nmog_evap_ustons

                            factor = vmt_liquid_fuel / grams_per_metric_ton
                            ch4_vehicle_metrictons += ch4 * factor
                            n2o_vehicle_metrictons += n2o * factor
                            co2_vehicle_metrictons += onroad_direct_co2e_grams_per_mile * factor

                    # other vehicle emissions
                    pm25_brakewear_ustons += (vmt_liquid_fuel * pm25_brakewear_l + vmt_electricity * pm25_brakewear_e) \
                                             / grams_per_us_ton
                    pm25_tirewear_ustons += (vmt_liquid_fuel * pm25_tirewear_l + vmt_electricity * pm25_tirewear_e) \
                                            / grams_per_us_ton

                    pm25_vehicle_ustons = pm25_tailpipe_ustons + pm25_brakewear_ustons + pm25_tirewear_ustons

                    # calc upstream emissions for both liquid and electric fuel operation
                    kwhs, gallons = fuel_generation_kWh, fuel_consumption_gallons
                    # voc_upstream_ustons = (kwhs * voc_ps + gallons * voc_ref) / grams_per_us_ton
                    co_upstream_ustons = (kwhs * co_egu + gallons * co_ref) / grams_per_us_ton
                    nox_upstream_ustons = (kwhs * nox_egu + gallons * nox_ref) / grams_per_us_ton
                    pm25_upstream_ustons = (kwhs * pm25_egu + gallons * pm25_ref) / grams_per_us_ton
                    sox_upstream_ustons = (kwhs * sox_egu + gallons * sox_ref) / grams_per_us_ton
                    # benzene_upstream_ustons = (kwhs * benzene_ps + gallons * benzene_ref) / grams_per_us_ton
                    # butadiene13_upstream_ustons = (kwhs * butadiene13_ps + gallons * butadiene13_ref) / grams_per_us_ton
                    # formaldehyde_upstream_ustons = (kwhs * formaldehyde_ps + gallons * formaldehyde_ref) / grams_per_us_ton
                    # acetaldehyde_upstream_ustons = (kwhs * acetaldehyde_ps + gallons * acetaldehyde_ref) / grams_per_us_ton
                    # acrolein_upstream_ustons = (kwhs * acrolein_ps + gallons * acrolein_ref) / grams_per_us_ton

                    co2_upstream_metrictons = (kwhs * co2_egu + gallons * co2_ref) / grams_per_metric_ton
                    ch4_upstream_metrictons = (kwhs * ch4_egu + gallons * ch4_ref) / grams_per_metric_ton
                    n2o_upstream_metrictons = (kwhs * n2o_egu + gallons * n2o_ref) / grams_per_metric_ton

                    # sum tailpipe and upstream into totals
                    # voc_total_ustons = voc_tailpipe_ustons + voc_upstream_ustons
                    nmog_total_ustons = nmog_vehicle_ustons # + nmog_upstream_ustons
                    co_total_ustons = co_vehicle_ustons + co_upstream_ustons
                    nox_total_ustons = nox_vehicle_ustons + nox_upstream_ustons
                    pm25_total_ustons = pm25_vehicle_ustons + pm25_upstream_ustons
                    sox_total_ustons = sox_vehicle_ustons + sox_upstream_ustons
                    # benzene_total_ustons = benzene_tailpipe_ustons + benzene_upstream_ustons
                    # butadiene13_total_ustons = butadiene13_tailpipe_ustons + butadiene13_upstream_ustons
                    # formaldehyde_total_ustons = formaldehyde_tailpipe_ustons + formaldehyde_upstream_ustons
                    # acetaldehyde_total_ustons = acetaldehyde_tailpipe_ustons + acetaldehyde_upstream_ustons
                    # acrolein_total_ustons = acrolein_tailpipe_ustons + acrolein_upstream_ustons
                    co2_total_metrictons = co2_vehicle_metrictons + co2_upstream_metrictons
                    ch4_total_metrictons = ch4_vehicle_metrictons + ch4_upstream_metrictons
                    n2o_total_metrictons = n2o_vehicle_metrictons + n2o_upstream_metrictons

                    # calc energy security related attributes and comparisons to year_for_compares
                    oil_bbl = fuel_consumption_gallons * e0_share * e0_energy_density_ratio / gal_per_bbl
                    imported_oil_bbl = oil_bbl * get_energysecurity_cf(calendar_year)
                    imported_oil_bbl_per_day = imported_oil_bbl / 365
                    # share_of_us_annual_gasoline = fuel_consumption_gallons / gallons_of_gasoline_us_annual
                    # share_of_us_annual_oil = oil_bbl / bbl_oil_us_annual

                    # calc kwh and comparisons to year_for_compares
                    # share_of_us_annual_kwh = fuel_generation_kWh / kwh_us_annual

                    if vmt_liquid_fuel > 0 or vmt_electricity > 0:
                        flag = 1

                    vehicle_effects_dict.update({
                        'session_name': omega_globals.options.session_name,
                        'vehicle_id': vehicle_id,
                        'manufacturer_id': mfr_id,
                        'name': name,
                        'calendar_year': int(calendar_year),
                        'model_year': calendar_year - age,
                        'age': age,
                        'base_year_reg_class_id': base_year_reg_class_id,
                        'reg_class_id': reg_class_id,
                        'in_use_fuel_id': in_use_fuel_id,
                        'market_class_id': market_class_id,
                        'fueling_class': fueling_class,
                        'base_year_powertrain_type': base_year_powertrain_type,
                        'body_style': body_style,
                        'registered_count': vad['registered_count'],
                        'vmt_adjustment': calendar_year_vmt_adj,
                        'annual_vmt': annual_vmt,
                        'odometer': odometer,
                        'vmt': vmt,
                        'vmt_liquid_fuel': vmt_liquid_fuel,
                        'vmt_electricity': vmt_electricity,
                        'onroad_direct_co2e_grams_per_mile': onroad_direct_co2e_grams_per_mile,
                        'onroad_direct_kwh_per_mile': onroad_direct_kwh_per_mile,
                        'onroad_gallons_per_mile': onroad_gallons_per_mile,
                        'fuel_consumption_gallons': fuel_consumption_gallons,
                        'fuel_consumption_kWh': fuel_consumption_kWh,
                        'fuel_generation_kWh': fuel_generation_kWh,

                        # f'share_of_{year_for_compares}_US_gasoline': share_of_us_annual_gasoline,
                        # f'share_of_{year_for_compares}_US_kWh': share_of_us_annual_kwh,
                        'barrels_of_oil': oil_bbl,
                        # f'share_of_{year_for_compares}_US_oil': share_of_us_annual_oil,
                        'barrels_of_imported_oil': imported_oil_bbl,
                        'barrels_of_imported_oil_per_day': imported_oil_bbl_per_day,

                        'session_fatalities': session_fatalities,

                        # 'voc_tailpipe_ustons': voc_tailpipe_ustons,
                        'nmog_tailpipe_ustons': nmog_tailpipe_ustons,
                        'nmog_evaporative_ustons': nmog_evap_ustons,
                        'nmog_vehicle_ustons': nmog_vehicle_ustons,
                        'co_vehicle_ustons': co_vehicle_ustons,
                        'nox_vehicle_ustons': nox_vehicle_ustons,
                        'pm25_tailpipe_ustons': pm25_tailpipe_ustons,
                        'pm25_brakewear_ustons': pm25_brakewear_ustons,
                        'pm25_tirewear_ustons': pm25_tirewear_ustons,
                        'pm25_vehicle_ustons': pm25_vehicle_ustons,
                        'sox_vehicle_ustons': sox_vehicle_ustons,
                        # 'benzene_tailpipe_ustons': benzene_tailpipe_ustons,
                        # 'butadiene13_tailpipe_ustons': butadiene13_tailpipe_ustons,
                        # 'formaldehyde_tailpipe_ustons': formaldehyde_tailpipe_ustons,
                        # 'acetaldehyde_tailpipe_ustons': acetaldehyde_tailpipe_ustons,
                        # 'acrolein_tailpipe_ustons': acrolein_tailpipe_ustons,

                        'ch4_vehicle_metrictons': ch4_vehicle_metrictons,
                        'n2o_vehicle_metrictons': n2o_vehicle_metrictons,
                        'co2_vehicle_metrictons': co2_vehicle_metrictons,

                        # 'voc_upstream_ustons': voc_upstream_ustons,
                        'co_upstream_ustons': co_upstream_ustons,
                        'nox_upstream_ustons': nox_upstream_ustons,
                        'pm25_upstream_ustons': pm25_upstream_ustons,
                        'sox_upstream_ustons': sox_upstream_ustons,
                        # 'benzene_upstream_ustons': benzene_upstream_ustons,
                        # 'butadiene13_upstream_ustons': butadiene13_upstream_ustons,
                        # 'formaldehyde_upstream_ustons': formaldehyde_upstream_ustons,
                        # 'acetaldehyde_upstream_ustons': acetaldehyde_upstream_ustons,
                        # 'acrolein_upstream_ustons': acrolein_upstream_ustons,

                        'co2_upstream_metrictons': co2_upstream_metrictons,
                        'ch4_upstream_metrictons': ch4_upstream_metrictons,
                        'n2o_upstream_metrictons': n2o_upstream_metrictons,

                        # 'voc_total_ustons': voc_total_ustons,
                        'nmog_total_ustons': nmog_total_ustons,
                        'co_total_ustons': co_total_ustons,
                        'nox_total_ustons': nox_total_ustons,
                        'pm25_total_ustons': pm25_total_ustons,
                        'sox_total_ustons': sox_total_ustons,
                        # 'benzene_total_ustons': benzene_total_ustons,
                        # 'butadiene13_total_ustons': butadiene13_total_ustons,
                        # 'formaldehyde_total_ustons': formaldehyde_total_ustons,
                        # 'acetaldehyde_total_ustons': acetaldehyde_total_ustons,
                        # 'acrolein_total_ustons': acrolein_total_ustons,
                        'co2_total_metrictons': co2_total_metrictons,
                        'ch4_total_metrictons': ch4_total_metrictons,
                        'n2o_total_metrictons': n2o_total_metrictons,
                    }
                    )
                if flag:
                    key = (vehicle_id, calendar_year, age)
                    calendar_year_effects_dict[key] = vehicle_effects_dict

        physical_effects_dict.update(calendar_year_effects_dict)

    return physical_effects_dict


def calc_annual_physical_effects(input_df):
    """

    Args:
        input_df: DataFrame of physical effects by vehicle.

    Returns:
        A DataFrame of physical effects by calendar year.

    """
    from context.onroad_fuels import OnroadFuel

    grams_per_metric_ton = get_inputs_for_effects(arg='grams_per_metric_ton')
    calendar_years = input_df['calendar_year'].unique()
    d = dict()
    num = 0
    for calendar_year in calendar_years:
        d[num] = {
            'calendar_year': calendar_year,
            'transmission_efficiency': OnroadFuel.get_fuel_attribute(calendar_year, 'US electricity',
                                                                     'transmission_efficiency')
        }
        num += 1

    elec_trans_efficiency = pd.DataFrame(d).transpose()

    attributes = [col for col in input_df.columns if ('vmt' in col or 'vmt_' in col) and '_vmt' not in col]
    additional_attributes = ['count', 'consumption', 'generation', 'barrels', 'tons', 'fatalit']
    for additional_attribute in additional_attributes:
        for col in input_df:
            if col.__contains__(additional_attribute):
                attributes.append(col)

    # groupby calendar year, regclass and fueling class
    groupby_cols = ['session_name', 'calendar_year', 'reg_class_id', 'fueling_class']
    return_df = input_df[[*groupby_cols, *attributes]]
    return_df = return_df.groupby(by=groupby_cols, axis=0, as_index=False).sum()
    return_df = return_df.merge(elec_trans_efficiency, on='calendar_year', how='left')

    return_df.insert(return_df.columns.get_loc('fuel_generation_kWh') + 1,
                     'onroad_gallons_per_mile',
                     return_df['fuel_consumption_gallons'] / return_df['vmt_liquid_fuel'])

    return_df.insert(return_df.columns.get_loc('fuel_generation_kWh') + 1,
                     'onroad_direct_kwh_per_mile',
                     return_df['fuel_consumption_kWh'] * return_df['transmission_efficiency'] / return_df['vmt_electricity'])

    return_df.insert(return_df.columns.get_loc('fuel_generation_kWh') + 1,
                     'onroad_direct_co2e_grams_per_mile',
                     return_df['co2_vehicle_metrictons'] * grams_per_metric_ton / return_df['vmt_liquid_fuel'])

    attributes += ['onroad_gallons_per_mile',
                   'onroad_direct_kwh_per_mile',
                   'onroad_direct_co2e_grams_per_mile']

    return_df.drop(columns='transmission_efficiency', inplace=True)

    # groupby calendar year and regclass
    groupby_cols = ['session_name', 'calendar_year', 'reg_class_id']
    yr_rc_df = input_df[[*groupby_cols, *attributes]]
    yr_rc_df = yr_rc_df.groupby(by=groupby_cols, axis=0, as_index=False).sum()
    yr_rc_df.insert(yr_rc_df.columns.get_loc('reg_class_id') + 1, 'fueling_class', 'ALL')

    # groupby calendar year and fueling class
    groupby_cols = ['session_name', 'calendar_year', 'fueling_class']
    yr_fc_df = input_df[[*groupby_cols, *attributes]]
    yr_fc_df = yr_fc_df.groupby(by=groupby_cols, axis=0, as_index=False).sum()
    yr_fc_df.insert(yr_fc_df.columns.get_loc('fueling_class') - 1, 'reg_class_id', 'ALL')

    # groupby calendar year
    groupby_cols = ['session_name', 'calendar_year']
    yr_df = input_df[[*groupby_cols, *attributes]]
    yr_df = yr_df.groupby(by=groupby_cols, axis=0, as_index=False).sum()
    yr_df.insert(yr_df.columns.get_loc('calendar_year') + 1, 'fueling_class', 'ALL')
    yr_df.insert(yr_df.columns.get_loc('calendar_year') + 1, 'reg_class_id', 'ALL')

    for df in [yr_rc_df, yr_fc_df, yr_df]:
        df['onroad_gallons_per_mile'] = df['fuel_consumption_gallons'] / df['vmt']
        df['onroad_direct_kwh_per_mile'] = df['fuel_consumption_kWh'] / df['vmt']
        df['onroad_direct_co2e_grams_per_mile'] = df['co2_vehicle_metrictons'] * grams_per_metric_ton / df['vmt']

    return_df = pd.concat([return_df, yr_rc_df, yr_fc_df, yr_df], axis=0, ignore_index=True)

    # calc additional attributes
    # input_attributes_list = ['gallons_of_gasoline_us_annual', 'bbl_oil_us_annual', 'kwh_us_annual', 'year_for_compares']

    # gallons_of_gasoline_us_annual, bbl_oil_us_annual, kwh_us_annual, year_for_compares = get_inputs_for_effects(*input_attributes_list)
    # year_for_compares = int(year_for_compares)

    # share_of_us_annual_gasoline = return_df['fuel_consumption_gallons'] / gallons_of_gasoline_us_annual
    # share_of_us_annual_oil = return_df['barrels_of_oil'] / bbl_oil_us_annual
    # share_of_us_annual_kwh = return_df['fuel_generation_kWh'] / kwh_us_annual

    # return_df.insert(return_df.columns.get_loc('fuel_generation_kWh') + 1, f'share_of_{year_for_compares}_US_kWh', share_of_us_annual_kwh)
    # return_df.insert(return_df.columns.get_loc('fuel_generation_kWh') + 1, f'share_of_{year_for_compares}_US_gasoline', share_of_us_annual_gasoline)
    # return_df.insert(return_df.columns.get_loc('barrels_of_oil') + 1, f'share_of_{year_for_compares}_US_oil', share_of_us_annual_oil)

    return return_df

def calc_legacy_fleet_physical_effects(legacy_fleet_safety_effects_dict): #, adjusted_vmt):
    """

    Args:
        legacy_fleet_safety_effects_dictv: The legacy_fleet dictionary generated via the safety_effects module.
        adjusted_vmt: object; an object of the AdjustmentsVMT class.

    Returns:
        A dictionary key, value pair where the key is a tuple (vehicle_id, calendar_year, age) and the value is a dictionary of key, value pairs providing
        vehicle attributes (e.g., model_year, reg_class_id, in_use_fuel_id, etc.) and inventory attributes (e.g., co2 tons, fuel consumed, etc.) and their attribute values.

    Note:
        This function must not be called until AFTER calc_physical_effects so that the EGU rates will have been
        generated there using energy consumption there.

    """
    from effects.legacy_fleet import LegacyFleet
    from context.onroad_fuels import OnroadFuel
    from common.omega_eval import Eval

    grams_per_us_ton, grams_per_metric_ton, gal_per_bbl, e0_share, e0_energy_density_ratio = get_inputs_for_effects()

    physical_effects_dict = dict()
    for key, nested_dict in LegacyFleet._legacy_fleet.items():

        vehicle_effects_dict = dict()

        vehicle_id, calendar_year, age = key

        # get vmt and session fatalities from safety_effects_dict
        safety_effects_key = (vehicle_id, calendar_year, age)
        session_fatalities \
            = legacy_fleet_safety_effects_dict[safety_effects_key]['session_fatalities']
        vmt = legacy_fleet_safety_effects_dict[safety_effects_key]['vmt']
        annual_vmt = legacy_fleet_safety_effects_dict[safety_effects_key]['annual_vmt']
        odometer = legacy_fleet_safety_effects_dict[safety_effects_key]['odometer']
        calendar_year_vmt_adj = legacy_fleet_safety_effects_dict[safety_effects_key]['vmt_adjustment']

        model_year = nested_dict['model_year']
        reg_class_id = nested_dict['reg_class_id']
        market_class_id = nested_dict['market_class_id']
        in_use_fuel_id = nested_dict['in_use_fuel_id']
        miles_per_gallon = nested_dict['miles_per_gallon']
        kwh_per_mile = nested_dict['kwh_per_mile']
        onroad_miles_per_gallon = miles_per_gallon * 0.8
        try:
            onroad_co2_grams_per_mile = 8887 / onroad_miles_per_gallon
            onroad_gallons_per_mile = 1 / onroad_miles_per_gallon
        except ZeroDivisionError:
            onroad_co2_grams_per_mile = 0
            onroad_gallons_per_mile = 0

        onroad_kwh_per_mile = kwh_per_mile / 0.7

        safety_dict_key = (vehicle_id, calendar_year, age)

        nmog_tailpipe_ustons = nmog_evap_ustons = nmog_vehicle_ustons = 0
        co_vehicle_ustons = nox_vehicle_ustons = sox_vehicle_ustons = 0
        pm25_tailpipe_ustons = pm25_brakewear_ustons = pm25_tirewear_ustons = pm25_vehicle_ustons = 0
        # benzene_tailpipe_ustons = butadiene13_tailpipe_ustons = formaldehyde_tailpipe_ustons \
        #     = acetaldehyde_tailpipe_ustons = acrolein_tailpipe_ustons = 0

        pm25_brakewear_rate = pm25_tirewear_rate = 0
        pm25_exhaust_rate = nmog_rate = co_rate = nox_rate = sox_rate = ch4_rate = n2o_rate = 0
        nmog_permeation_rate = nmog_venting_rate = nmog_leaks_rate = nmog_refuel_disp_rate = nmog_refuel_spill_rate = 0

        voc_ref_rate = co_ref_rate = nox_ref_rate = pm25_ref_rate = sox_ref_rate = 0
        co2_ref_rate = ch4_ref_rate = n2o_ref_rate = 0
        # benzene_ref = butadiene13_ref = formaldehyde_ref = acetaldehyde_ref = acrolein_ref = 0

        co_egu_rate = nox_egu_rate = pm25_egu_rate = sox_egu_rate = co2_egu_rate = ch4_egu_rate = n2o_egu_rate = 0

        ch4_vehicle_metrictons = n2o_vehicle_metrictons = co2_vehicle_metrictons = 0

        vmt_electricity = vmt_liquid_fuel = transmission_efficiency = 0

        sourcetype_name = 'passenger car'
        if reg_class_id == 'truck':
            sourcetype_name = 'passenger truck'

        veh_rates_by = 'age'  # for now; set as an input if we want to; value can be 'age' or 'odometer'
        ind_var_value = pd.to_numeric(age)
        if veh_rates_by == 'odometer':
            ind_var_value = pd.to_numeric(odometer)

        fuel_dict = Eval.eval(in_use_fuel_id, {'__builtins__': None}, {})
        for fuel, fuel_share in fuel_dict.items():

            if 'electric' in fuel:
                vmt_electricity = vmt
                pm25_brakewear_rate, pm25_tirewear_rate \
                    = get_vehicle_emission_rate(model_year, sourcetype_name, reg_class_id, fuel, ind_var_value)

                # the energy consumption and generation values do not matter here, so set to 0
                co_egu_rate, nox_egu_rate, pm25_egu_rate, sox_egu_rate, co2_egu_rate, ch4_egu_rate, n2o_egu_rate \
                    = get_egu_emission_rate(calendar_year, 0, 0)

            elif 'gasoline' in fuel:
                vmt_liquid_fuel = vmt
                pm25_brakewear_rate, pm25_tirewear_rate, pm25_exhaust_rate, \
                nmog_rate, nmog_permeation_rate, nmog_venting_rate, nmog_leaks_rate, nmog_refuel_disp_rate, nmog_refuel_spill_rate, \
                co_rate, nox_rate, sox_rate, ch4_rate, n2o_rate \
                    = get_vehicle_emission_rate(model_year, sourcetype_name, reg_class_id, fuel, ind_var_value)

                voc_ref_rate, co_ref_rate, nox_ref_rate, pm25_ref_rate, sox_ref_rate, co2_ref_rate, ch4_ref_rate, n2o_ref_rate \
                    = get_refinery_ef(calendar_year, fuel)

            elif 'diesel' in fuel:
                vmt_liquid_fuel = vmt
                pm25_brakewear_rate, pm25_tirewear_rate, pm25_exhaust_rate, \
                nmog_rate, nmog_refuel_spill_rate, \
                co_rate, nox_rate, sox_rate, ch4_rate, n2o_rate \
                    = get_vehicle_emission_rate(model_year, sourcetype_name, reg_class_id, fuel, ind_var_value)

                voc_ref_rate, co_ref_rate, nox_ref_rate, pm25_ref_rate, sox_ref_rate, co2_ref_rate, ch4_ref_rate, n2o_ref_rate \
                    = get_refinery_ef(calendar_year, fuel)

            transmission_efficiency = OnroadFuel.get_fuel_attribute(calendar_year, fuel, 'transmission_efficiency')

        fuel_consumption_kWh = vmt * onroad_kwh_per_mile
        fuel_generation_kWh = fuel_consumption_kWh / transmission_efficiency
        fuel_consumption_gallons = vmt * onroad_gallons_per_mile

        # calc tailpipe emissions
        factor = vmt / grams_per_us_ton
        nmog_tailpipe_ustons += nmog_rate * factor
        co_vehicle_ustons += co_rate * factor
        nox_vehicle_ustons += nox_rate * factor
        pm25_tailpipe_ustons += pm25_exhaust_rate * factor
        # benzene_tailpipe_ustons += benzene * factor
        # butadiene13_tailpipe_ustons += butadiene13 * factor
        # formaldehyde_tailpipe_ustons += formaldehyde * factor
        # acetaldehyde_tailpipe_ustons += acetaldehyde * factor
        # acrolein_tailpipe_ustons += acrolein * factor

        factor = fuel_consumption_gallons / grams_per_us_ton
        sox_vehicle_ustons += sox_rate * factor
        nmog_evap_ustons += sum([nmog_permeation_rate,
                                 nmog_venting_rate,
                                 nmog_leaks_rate,
                                 nmog_refuel_disp_rate,
                                 nmog_refuel_spill_rate]) * factor

        nmog_vehicle_ustons = nmog_tailpipe_ustons + nmog_evap_ustons

        factor = vmt / grams_per_metric_ton
        ch4_vehicle_metrictons += ch4_rate * factor
        n2o_vehicle_metrictons += n2o_rate * factor
        co2_vehicle_metrictons += onroad_co2_grams_per_mile * factor

        # other vehicle emissions
        pm25_brakewear_ustons += vmt * pm25_brakewear_rate / grams_per_us_ton
        pm25_tirewear_ustons += vmt * pm25_tirewear_rate / grams_per_us_ton

        pm25_vehicle_ustons = pm25_tailpipe_ustons + pm25_brakewear_ustons + pm25_tirewear_ustons

        # calc upstream emissions for both liquid and electric fuel operation
        kwhs, gallons = fuel_generation_kWh, fuel_consumption_gallons
        # voc_upstream_ustons = (kwhs * voc_ps + gallons * voc_ref) / grams_per_us_ton
        co_upstream_ustons = (kwhs * co_egu_rate + gallons * co_ref_rate) / grams_per_us_ton
        nox_upstream_ustons = (kwhs * nox_egu_rate + gallons * nox_ref_rate) / grams_per_us_ton
        pm25_upstream_ustons = (kwhs * pm25_egu_rate + gallons * pm25_ref_rate) / grams_per_us_ton
        sox_upstream_ustons = (kwhs * sox_egu_rate + gallons * sox_ref_rate) / grams_per_us_ton
        # benzene_upstream_ustons = (kwhs * benzene_ps + gallons * benzene_ref) / grams_per_us_ton
        # butadiene13_upstream_ustons = (kwhs * butadiene13_ps + gallons * butadiene13_ref) / grams_per_us_ton
        # formaldehyde_upstream_ustons = (kwhs * formaldehyde_ps + gallons * formaldehyde_ref) / grams_per_us_ton
        # acetaldehyde_upstream_ustons = (kwhs * acetaldehyde_ps + gallons * acetaldehyde_ref) / grams_per_us_ton
        # acrolein_upstream_ustons = (kwhs * acrolein_ps + gallons * acrolein_ref) / grams_per_us_ton

        co2_upstream_metrictons = (kwhs * co2_egu_rate + gallons * co2_ref_rate) / grams_per_metric_ton
        ch4_upstream_metrictons = (kwhs * ch4_egu_rate + gallons * ch4_ref_rate) / grams_per_metric_ton
        n2o_upstream_metrictons = (kwhs * n2o_egu_rate + gallons * n2o_ref_rate) / grams_per_metric_ton

        # sum tailpipe and upstream into totals
        # voc_total_ustons = voc_tailpipe_ustons + voc_upstream_ustons
        nmog_total_ustons = nmog_vehicle_ustons # + nmog_upstream_ustons
        co_total_ustons = co_vehicle_ustons + co_upstream_ustons
        nox_total_ustons = nox_vehicle_ustons + nox_upstream_ustons
        pm25_total_ustons = pm25_vehicle_ustons + pm25_upstream_ustons
        sox_total_ustons = sox_vehicle_ustons + sox_upstream_ustons
        # benzene_total_ustons = benzene_tailpipe_ustons + benzene_upstream_ustons
        # butadiene13_total_ustons = butadiene13_tailpipe_ustons + butadiene13_upstream_ustons
        # formaldehyde_total_ustons = formaldehyde_tailpipe_ustons + formaldehyde_upstream_ustons
        # acetaldehyde_total_ustons = acetaldehyde_tailpipe_ustons + acetaldehyde_upstream_ustons
        # acrolein_total_ustons = acrolein_tailpipe_ustons + acrolein_upstream_ustons
        co2_total_metrictons = co2_vehicle_metrictons + co2_upstream_metrictons
        ch4_total_metrictons = ch4_vehicle_metrictons + ch4_upstream_metrictons
        n2o_total_metrictons = n2o_vehicle_metrictons + n2o_upstream_metrictons

        # calc energy security related attributes and comparisons to year_for_compares
        oil_bbl = fuel_consumption_gallons * e0_share * e0_energy_density_ratio / gal_per_bbl
        imported_oil_bbl = oil_bbl * get_energysecurity_cf(calendar_year)
        imported_oil_bbl_per_day = imported_oil_bbl / 365
        # share_of_us_annual_gasoline = fuel_consumption_gallons / gallons_of_gasoline_us_annual
        # share_of_us_annual_oil = oil_bbl / bbl_oil_us_annual

        # calc kwh and comparisons to year_for_compares
        # share_of_us_annual_kwh = fuel_generation_kWh / kwh_us_annual

        vehicle_effects_dict.update({
            'session_name': omega_globals.options.session_name,
            'vehicle_id': vehicle_id,
            'manufacturer_id': legacy_fleet_safety_effects_dict[safety_dict_key]['manufacturer_id'],
            'name': legacy_fleet_safety_effects_dict[safety_dict_key]['name'],
            'calendar_year': calendar_year,
            'model_year': model_year,
            'age': age,
            'base_year_reg_class_id': reg_class_id,
            'reg_class_id': reg_class_id,
            'in_use_fuel_id': in_use_fuel_id,
            'market_class_id': market_class_id,
            'fueling_class': legacy_fleet_safety_effects_dict[safety_dict_key]['fueling_class'],
            'base_year_powertrain_type': legacy_fleet_safety_effects_dict[safety_dict_key]['base_year_powertrain_type'],
            'body_style': legacy_fleet_safety_effects_dict[safety_dict_key]['body_style'],
            'registered_count': legacy_fleet_safety_effects_dict[safety_dict_key]['registered_count'],
            'vmt_adjustment': calendar_year_vmt_adj,
            'annual_vmt': annual_vmt,
            'odometer': odometer,
            'vmt': vmt,
            'vmt_liquid_fuel': vmt_liquid_fuel,
            'vmt_electricity': vmt_electricity,
            'onroad_direct_co2e_grams_per_mile': onroad_co2_grams_per_mile,
            'onroad_direct_kwh_per_mile': onroad_kwh_per_mile,
            'onroad_gallons_per_mile': onroad_gallons_per_mile,
            'fuel_consumption_gallons': fuel_consumption_gallons,
            'fuel_consumption_kWh': fuel_consumption_kWh,
            'fuel_generation_kWh': fuel_generation_kWh,

            # f'share_of_{year_for_compares}_US_gasoline': share_of_us_annual_gasoline,
            # f'share_of_{year_for_compares}_US_kWh': share_of_us_annual_kwh,
            'barrels_of_oil': oil_bbl,
            # f'share_of_{year_for_compares}_US_oil': share_of_us_annual_oil,
            'barrels_of_imported_oil': imported_oil_bbl,
            'barrels_of_imported_oil_per_day': imported_oil_bbl_per_day,

            'session_fatalities': session_fatalities,

            # 'voc_tailpipe_ustons': voc_tailpipe_ustons,
            'nmog_tailpipe_ustons': nmog_tailpipe_ustons,
            'nmog_evaporative_ustons': nmog_evap_ustons,
            'nmog_vehicle_ustons': nmog_vehicle_ustons,
            'co_vehicle_ustons': co_vehicle_ustons,
            'nox_vehicle_ustons': nox_vehicle_ustons,
            'pm25_tailpipe_ustons': pm25_tailpipe_ustons,
            'pm25_brakewear_ustons': pm25_brakewear_ustons,
            'pm25_tirewear_ustons': pm25_tirewear_ustons,
            'pm25_vehicle_ustons': pm25_vehicle_ustons,
            'sox_vehicle_ustons': sox_vehicle_ustons,
            # 'benzene_tailpipe_ustons': benzene_tailpipe_ustons,
            # 'butadiene13_tailpipe_ustons': butadiene13_tailpipe_ustons,
            # 'formaldehyde_tailpipe_ustons': formaldehyde_tailpipe_ustons,
            # 'acetaldehyde_tailpipe_ustons': acetaldehyde_tailpipe_ustons,
            # 'acrolein_tailpipe_ustons': acrolein_tailpipe_ustons,

            'ch4_vehicle_metrictons': ch4_vehicle_metrictons,
            'n2o_vehicle_metrictons': n2o_vehicle_metrictons,
            'co2_vehicle_metrictons': co2_vehicle_metrictons,

            # 'voc_upstream_ustons': voc_upstream_ustons,
            'co_upstream_ustons': co_upstream_ustons,
            'nox_upstream_ustons': nox_upstream_ustons,
            'pm25_upstream_ustons': pm25_upstream_ustons,
            'sox_upstream_ustons': sox_upstream_ustons,
            # 'benzene_upstream_ustons': benzene_upstream_ustons,
            # 'butadiene13_upstream_ustons': butadiene13_upstream_ustons,
            # 'formaldehyde_upstream_ustons': formaldehyde_upstream_ustons,
            # 'acetaldehyde_upstream_ustons': acetaldehyde_upstream_ustons,
            # 'acrolein_upstream_ustons': acrolein_upstream_ustons,

            'co2_upstream_metrictons': co2_upstream_metrictons,
            'ch4_upstream_metrictons': ch4_upstream_metrictons,
            'n2o_upstream_metrictons': n2o_upstream_metrictons,

            # 'voc_total_ustons': voc_total_ustons,
            'nmog_total_ustons': nmog_total_ustons,
            'co_total_ustons': co_total_ustons,
            'nox_total_ustons': nox_total_ustons,
            'pm25_total_ustons': pm25_total_ustons,
            'sox_total_ustons': sox_total_ustons,
            # 'benzene_total_ustons': benzene_total_ustons,
            # 'butadiene13_total_ustons': butadiene13_total_ustons,
            # 'formaldehyde_total_ustons': formaldehyde_total_ustons,
            # 'acetaldehyde_total_ustons': acetaldehyde_total_ustons,
            # 'acrolein_total_ustons': acrolein_total_ustons,
            'co2_total_metrictons': co2_total_metrictons,
            'ch4_total_metrictons': ch4_total_metrictons,
            'n2o_total_metrictons': n2o_total_metrictons,
        }
        )
        key = (vehicle_id, calendar_year, age)
        physical_effects_dict[key] = vehicle_effects_dict

    return physical_effects_dict
