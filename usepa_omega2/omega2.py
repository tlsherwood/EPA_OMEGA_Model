"""
omega2.py
=========

OMEGA2 top level code

"""

import o2  # import global variables
from usepa_omega2 import *
from omega_plot import *
import os

def run_postproc():
    from manufacturer_annual_data import ManufacturerAnnualData
    from vehicles import Vehicle
    from vehicle_annual_data import VehicleAnnualData

    calendar_year = sql_unpack_result(o2.session.query(ManufacturerAnnualData.calendar_year).all())
    cert_target_co2_Mg = o2.session.query(ManufacturerAnnualData.cert_target_co2_Mg).all()
    cert_co2_Mg = o2.session.query(ManufacturerAnnualData.cert_co2_Mg).all()
    total_cost_billions = float(
        o2.session.query(func.sum(ManufacturerAnnualData.manufacturer_vehicle_cost_dollars)).scalar()) / 1e9

    fig, ax1 = fplothg(calendar_year, cert_target_co2_Mg, '.-')
    ax1.plot(calendar_year, cert_co2_Mg, '.-')
    label_xyt(ax1, 'Year', 'CO2 Mg', '%s\nCompliance Versus Calendar Year\n Total Cost $%.2f Billion' % (o2.options.session_name, total_cost_billions))
    fig.savefig(o2.options.output_folder + '%s Compliance v Year' % o2.options.session_name)

    bev_non_hauling_share_frac = o2.session.query(ManufacturerAnnualData.bev_non_hauling_share_frac).all()
    ice_non_hauling_share_frac = o2.session.query(ManufacturerAnnualData.ice_non_hauling_share_frac).all()
    bev_hauling_share_frac = o2.session.query(ManufacturerAnnualData.bev_hauling_share_frac).all()
    ice_hauling_share_frac = o2.session.query(ManufacturerAnnualData.ice_hauling_share_frac).all()

    fig, ax1 = fplothg(calendar_year, bev_non_hauling_share_frac, '.-')
    ax1.plot(calendar_year, ice_non_hauling_share_frac, '.-')
    ax1.plot(calendar_year, bev_hauling_share_frac, '.-')
    ax1.plot(calendar_year, ice_hauling_share_frac, '.-')
    label_xyt(ax1, 'Year', 'Market Share Frac', '%s\nMarket Shares' % o2.options.session_name)
    ax1.legend(['bev_non_hauling', 'ice_non_hauling', 'bev_hauling', 'ice_hauling'])
    fig.savefig(o2.options.output_folder + '%s Market Shares' % o2.options.session_name)

    fig, ax1 = figure()
    average_cost_data = dict()
    for hc in hauling_classes:
        average_cost_data[hc] = []
        for cy in calendar_year:
            average_cost_data[hc].append(o2.session.query(
                func.sum(Vehicle.new_vehicle_mfr_cost_dollars * VehicleAnnualData.registered_count) /
                func.sum(VehicleAnnualData.registered_count)). \
                                         filter(Vehicle.vehicle_ID == VehicleAnnualData.vehicle_ID). \
                                         filter(Vehicle.model_year == cy). \
                                         filter(Vehicle.hauling_class == hc). \
                                         filter(VehicleAnnualData.age == 0).scalar())
        ax1.plot(calendar_year, average_cost_data[hc])

    average_cost_data['total'] = []
    for cy in calendar_year:
        average_cost_data['total'].append(o2.session.query(
            func.sum(Vehicle.new_vehicle_mfr_cost_dollars * VehicleAnnualData.registered_count) /
            func.sum(VehicleAnnualData.registered_count)). \
                                     filter(Vehicle.vehicle_ID == VehicleAnnualData.vehicle_ID). \
                                     filter(Vehicle.model_year == cy). \
                                     filter(VehicleAnnualData.age == 0).scalar())
    ax1.plot(calendar_year, average_cost_data['total'])

    label_xyt(ax1, 'Year', 'Average Vehicle Cost [$]','%s\nAverage Vehicle Cost v Year' % o2.options.session_name)
    ax1.set_ylim(15e3, 50e3)
    ax1.legend(average_cost_data.keys())
    fig.savefig(o2.options.output_folder + '%s Average Vehicle Cost' % o2.options.session_name)


def run_omega(o2_options):
    import traceback
    import time

    start = time.time()

    print('OMEGA2 greets you, version %s' % code_version)
    if '__file__' in locals():
        print('from %s with love' % fileio.get_filenameext(__file__))

    # set up global variables:
    o2.options = o2_options
    init_omega_db()
    o2.engine.echo = o2.options.verbose
    omega_log.init_logfile()

    from fuels import Fuel
    from fuel_scenarios import FuelScenario
    from fuel_scenario_annual_data import FuelScenarioAnnualData
    from market_classes import MarketClass
    from cost_curves import CostCurve
    from cost_clouds import CostCloud
    from demanded_sales_annual_data import DemandedSalesAnnualData
    from manufacturers import Manufacturer
    from manufacturer_annual_data import ManufacturerAnnualData
    from vehicles import Vehicle
    from vehicle_annual_data import VehicleAnnualData
    from consumer.reregistration_fixed_by_age import ReregistrationFixedByAge
    from consumer.annual_vmt_fixed_by_age import AnnualVMTFixedByAge
    import consumer.sales as consumer
    import producer

    fileio.validate_folder(o2.options.output_folder)

    if o2.options.GHG_standard == 'flat':
        from GHG_standards_flat import GHGStandardFlat
    else:
        from GHG_standards_footprint import GHGStandardFootprint

    o2.options.producer_calculate_generalized_cost = producer.calculate_generalized_cost
    o2.options.consumer_calculate_generalized_cost = consumer.calculate_generalized_cost

    SQABase.metadata.create_all(o2.engine)

    init_fail = []
    try:
        init_fail = init_fail + Fuel.init_database_from_file(o2.options.fuels_file, verbose=o2.options.verbose)
        init_fail = init_fail + FuelScenario.init_database_from_file(o2.options.fuel_scenarios_file,
                                                                     verbose=o2.options.verbose)
        init_fail = init_fail + FuelScenarioAnnualData.init_database_from_file(
            o2.options.fuel_scenario_annual_data_file, verbose=o2.options.verbose)
        init_fail = init_fail + MarketClass.init_database_from_file(o2.options.market_classes_file,
                                                                    verbose=o2.options.verbose)

        if o2.options.cost_file_type == 'curves':
            init_fail = init_fail + CostCurve.init_database_from_file(o2.options.cost_file, verbose=o2.options.verbose)
        else:
            init_fail = init_fail + CostCloud.init_database_from_file(o2.options.cost_file, verbose=o2.options.verbose)

        if o2.options.GHG_standard == 'flat':
            init_fail = init_fail + GHGStandardFlat.init_database_from_file(o2.options.ghg_standards_file,
                                                                            verbose=o2.options.verbose)
            o2.options.GHG_standard = GHGStandardFlat
        else:
            init_fail = init_fail + GHGStandardFootprint.init_database_from_file(o2.options.ghg_standards_file,
                                                                                 verbose=o2.options.verbose)
            o2.options.GHG_standard = GHGStandardFootprint

        init_fail = init_fail + DemandedSalesAnnualData.init_database_from_file(
            o2.options.demanded_sales_annual_data_file, verbose=o2.options.verbose)
        init_fail = init_fail + Manufacturer.init_database_from_file(o2.options.manufacturers_file,
                                                                     verbose=o2.options.verbose)
        init_fail = init_fail + Vehicle.init_database_from_file(o2.options.vehicles_file, verbose=o2.options.verbose)

        if o2.options.stock_scrappage == 'fixed':
            init_fail = init_fail + ReregistrationFixedByAge.init_database_from_file(
                o2.options.reregistration_fixed_by_age_file, verbose=o2.options.verbose)
            o2.options.stock_scrappage = ReregistrationFixedByAge
        else:
            pass

        if o2.options.stock_vmt == 'fixed':
            init_fail = init_fail + AnnualVMTFixedByAge.init_database_from_file(o2.options.annual_vmt_fixed_by_age_file,
                                                                                verbose=o2.options.verbose)
            o2.options.stock_vmt = AnnualVMTFixedByAge
        else:
            pass

        # initial year = initial fleet model year (latest year of data)
        o2.options.analysis_initial_year = int(o2.session.query(func.max(Vehicle.model_year)).scalar()) + 1
        # final year = last year of cost curve data
        o2.options.analysis_final_year = int(o2.session.query(func.max(CostCurve.model_year)).scalar())

        if not init_fail:
            # dump_database_to_csv(engine, o2.options.database_dump_folder, verbose=False)
            producer.run_compliance_model()
            dump_omega_db_to_csv(o2.options.database_dump_folder)
            end = time.time()

            print('\nElapsed Time %.2f Seconds' % (end - start))
            run_postproc()
            # o2.session.close()
            o2.engine.dispose()
            o2.engine = None
            # o2.session = None
            o2.options = None
        else:
            omega_log.logwrite("\n#INIT FAIL")
    except Exception as e:
        if init_fail:
            omega_log.logwrite("\n#INIT FAIL")
        omega_log.logwrite("\n#RUNTIME FAIL\n%s\n" % traceback.format_exc())
        print("\n#RUNTIME FAIL\n%s\n" % traceback.format_exc())
        print("### Check OMEGA log for error messages ###")


def gui_comm(text):
    num_lines = sum(1 for line in open('gui/comm_file.txt'))
    file1 = open("gui/comm_file.txt", "a")  # append mode
    file1.write(str(num_lines + 1) + " " + text + " \n")
    file1.close()


if __name__ == "__main__":
    run_omega(OMEGARuntimeOptions())
