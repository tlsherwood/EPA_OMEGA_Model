"""
policy_fuel_upstream_methods.py
===============================


"""

print('importing %s' % __file__)

from usepa_omega2 import *


def upstream_zero(vehicle, cost_curve, co2_name, kwh_name):
    pass


def upstream_xev_ice_delta(vehicle, cost_curve, co2_name, kwh_name):
    from policy_fuel_upstream import PolicyFuelUpstream
    from fuels import Fuel

    upstream_gco2_per_kWh = PolicyFuelUpstream.get_upstream_co2e_grams_per_unit(vehicle.model_year, 'US electricity')
    upstream_inefficiency = PolicyFuelUpstream.get_upstream_inefficiency(vehicle.model_year, 'US electricity')
    upstream_gco2_per_gal = PolicyFuelUpstream.get_upstream_co2e_grams_per_unit(vehicle.model_year, 'pump gasoline')
    gco2_per_gal = Fuel.get_fuel_attributes('pump gasoline', 'co2_tailpipe_emissions_grams_per_unit')

    cost_curve[co2_name] += cost_curve[kwh_name] * upstream_gco2_per_kWh / (1 - upstream_inefficiency) - \
                            vehicle.cert_target_CO2_grams_per_mile * upstream_gco2_per_gal / gco2_per_gal


def upstream_actual(vehicle, cost_curve, co2_name, kwh_name):
    from policy_fuel_upstream import PolicyFuelUpstream
    upstream_gco2_per_kWh = PolicyFuelUpstream.get_upstream_co2e_grams_per_unit(vehicle.model_year, 'US electricity')
    upstream_inefficiency = PolicyFuelUpstream.get_upstream_inefficiency(vehicle.model_year, 'US electricity')
    upstream_gco2_per_gal = PolicyFuelUpstream.get_upstream_co2e_grams_per_unit(vehicle.model_year, 'pump gasoline')
    gco2_per_gal = Fuel.get_fuel_attributes('pump gasoline', 'co2_tailpipe_emissions_grams_per_unit')

    cost_curve[co2_name] += cost_curve[kwh_name] * upstream_gco2_per_kWh / (1 - upstream_inefficiency) + \
                            cost_curve[co2_name] * upstream_gco2_per_gal / gco2_per_gal


class PolicyFuelUpstreamMethods(OMEGABase):
    methods = pd.DataFrame()

    @staticmethod
    def get_upstream_method(calendar_year):
        return PolicyFuelUpstreamMethods.methods['upstream_calculation_method'].loc[
                  PolicyFuelUpstreamMethods.methods['calendar_year'] == calendar_year].item()

    @staticmethod
    def init_from_file(filename, verbose=False):
        if verbose:
            omega_log.logwrite('\nInitializing data from %s...' % filename)

        input_template_name = 'policy_upstream_method'
        input_template_version = 0.1
        input_template_columns = {'calendar_year', 'upstream_calculation_method'}

        template_errors = validate_template_version_info(filename, input_template_name, input_template_version,
                                                         verbose=verbose)

        if not template_errors:
            # read in the data portion of the input file
            df = pd.read_csv(filename, skiprows=1)

            template_errors = validate_template_columns(filename, input_template_columns, df.columns, verbose=verbose)

            if not template_errors:
                PolicyFuelUpstreamMethods.methods['calendar_year'] = df['calendar_year']
                PolicyFuelUpstreamMethods.methods['upstream_calculation_method'] = df['upstream_calculation_method']

        return template_errors


if __name__ == '__main__':
    try:
        if '__file__' in locals():
            print(fileio.get_filenameext(__file__))

        from fuels import Fuel

        # set up global variables:
        o2.options = OMEGARuntimeOptions()
        init_omega_db()
        o2.engine.echo = o2.options.verbose
        omega_log.init_logfile()

        SQABase.metadata.create_all(o2.engine)

        init_fail = []
        init_fail = init_fail + PolicyFuelUpstreamMethods.init_from_file(o2.options.fuel_upstream_methods_file,
                                                                  verbose=o2.options.verbose)

        if not init_fail:
            fileio.validate_folder(o2.options.database_dump_folder)
            PolicyFuelUpstreamMethods.methods.to_csv(
                o2.options.database_dump_folder + os.sep + 'policy_fuel_upstream_values.csv', index=False)

            print(PolicyFuelUpstreamMethods.get_upstream_method(2020))
            print(PolicyFuelUpstreamMethods.get_upstream_method(2027))
            print(PolicyFuelUpstreamMethods.get_upstream_method(2050))
        else:
            print(init_fail)
            print("\n#RUNTIME FAIL\n%s\n" % traceback.format_exc())
            os._exit(-1)
    except:
        print("\n#RUNTIME FAIL\n%s\n" % traceback.format_exc())
        os._exit(-1)
