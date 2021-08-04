"""

**Routines to load, access and apply off-cycle credit values**

Off-cycle credits represent GHG benefits of technologies that have no or limited on-cycle benefits.

For example, LED headlights have a real-world ("off-cycle") benefit but are not represented during certification
testing (tests are performed with headlights off).

As another example, engine Stop-Start has an on-cycle benefit but the vehicle idle duration during testing may
under-represent vehicle idle duration in real-world driving so there may be some additional benefit available.

----

**INPUT FILE FORMAT**

The file format consists of a one-row template header followed by a one-row data header and subsequent data
rows.  The data header uses a dynamic column notation, as detailed below.

The data represents offcycle credit values (grams CO2e/mile) credit group and regulatory class.

File Type
    comma-separated values (CSV)

Template Header
    .. csv-table::

       input_template_name:,offcycle_credits,input_template_version:,0.1

The data header consists of ``start_year``, ``credit_name``, ``credit_group``, ``credit_destination`` columns
followed by zero or more reg class columns, as needed.

Dynamic Data Header
    .. csv-table::
        :widths: auto

        start_year, credit_name, credit_group, credit_destination, ``reg_class_id:{reg_class_id}``, ...

Sample Data Columns
    .. csv-table::
        :widths: auto

        start_year,credit_name,credit_group,credit_destination,reg_class_id:car,reg_class_id:truck
        2020,start_stop,menu,cert_direct_offcycle_co2e_grams_per_mile,2.5,4.4
        2020,high_eff_alternator,menu,cert_direct_offcycle_co2e_grams_per_mile,2.7,2.7
        2020,ac_leakage,ac,cert_indirect_offcycle_co2e_grams_per_mile,13.8,17.2
        2020,ac_efficiency,ac,cert_direct_offcycle_co2e_grams_per_mile,5,7.2

Data Column Name and Description

:start_year:
    Start year of production constraint, constraint applies until the next available start year

:credit_name:
    Name of the offcycle credit

:credit_group:
    Group name of the offcycle credit, in case of limits within a group of credits (work in progress)

:credit_destination:
    Name of the vehicle CO2e attribute to apply the credit to, e.g. ``cert_direct_offcycle_co2e_grams_per_mile``, ``cert_indirect_offcycle_co2e_grams_per_mile``

**Optional Columns**

:``reg_class_id:{reg_class_id}``:
    The value of the credits.  Credits are specificied as positive numbers and are subtracted from the cert results to determine a compliance result

**CODE**

"""

print('importing %s' % __file__)

from omega_model import *


class OffCycleCredits(OMEGABase):
    """
    **Loads, stores and applies off-cycle credits to vehicle cost clouds**

    """

    _values = dict()

    offcycle_credit_names = []  #: list of credit names, populated during init, used to track credits across composition/decomposition and into the database, also used to check simulated vehicles for necessary columns
    offcycle_credit_groups = []  #: list of credit groups, populated during init
    offcycle_credit_value_columns = [] #: list of columns that contain credit values, of the format ``vehicle_attribute:attribute_value``

    @staticmethod
    def calc_off_cycle_credits(vehicle):
        """
        Calculate vehicle off-cycle credits for the vehicle's cost cloud

        Args:
            vehicle (Vehicle): the vehicle to apply off-cycle credits to

        Returns:
            vehicle.cost_cloud with off-cycle credits calculated

        """
        # TODO: off cycle groups can be used to apply credit limits by credit group
        group_totals = dict()
        for ocg in OffCycleCredits.offcycle_credit_groups:
            group_totals[ocg] = 0

        vehicle.cost_cloud['cert_direct_offcycle_co2e_grams_per_mile'] = 0
        vehicle.cost_cloud['cert_direct_offcycle_kwh_per_mile'] = 0
        vehicle.cost_cloud['cert_indirect_offcycle_co2e_grams_per_mile'] = 0

        for credit_column in OffCycleCredits.offcycle_credit_value_columns:
            attribute, value = credit_column.split(':')
            if vehicle.__getattribute__(attribute) == value:
                for offcycle_credit in OffCycleCredits.offcycle_credit_names:
                    start_years = OffCycleCredits._values[offcycle_credit]['start_year']
                    if len(start_years[start_years <= vehicle.model_year]) > 0:
                        credit_start_year = max(start_years[start_years <= vehicle.model_year])

                        credit_value = OffCycleCredits._values[offcycle_credit][credit_start_year][credit_column]
                        credit_destination = \
                            OffCycleCredits._values[offcycle_credit][credit_start_year]['credit_destination']

                        vehicle.cost_cloud[credit_destination] += credit_value * vehicle.cost_cloud[offcycle_credit]

        return vehicle.cost_cloud

    @classmethod
    def init_from_file(cls, filename, verbose=False):
        """

        Initialize class data from input file.

        Args:
            filename: name of input file
            verbose: enable additional console and logfile output if True

        Returns:
            List of template/input errors, else empty list on success

        """
        import numpy as np

        OffCycleCredits._values.clear()

        if verbose:
            omega_log.logwrite('\nInitializing data from %s...' % filename)

        input_template_name = 'offcycle_credits'
        input_template_version = 0.1
        input_template_columns = {'start_year', 'credit_name', 'credit_group', 'credit_destination'}

        template_errors = validate_template_version_info(filename, input_template_name, input_template_version,
                                                         verbose=verbose)

        if not template_errors:
            # read in the data portion of the input file
            df = pd.read_csv(filename, skiprows=1)

            template_errors = validate_template_columns(filename, input_template_columns, df.columns, verbose=verbose)

            if not template_errors:
                OffCycleCredits.offcycle_credit_value_columns = [c for c in df.columns if (':' in c)]

                for cc in OffCycleCredits.offcycle_credit_value_columns:
                    reg_class_id = cc.split(':')[1]
                    if reg_class_id not in omega_globals.options.RegulatoryClasses.reg_classes:
                        template_errors.append('*** Invalid Reg Class ID "%s" in %s ***' % (reg_class_id, filename))

                if not template_errors:
                    cls.offcycle_credit_names = df['credit_name'].unique().tolist()
                    cls.offcycle_credit_groups = df['credit_group'].unique().tolist()

                    for _, r in df.iterrows():
                        if r.credit_name not in OffCycleCredits._values:
                            OffCycleCredits._values[r.credit_name] = {
                                'start_year': np.array(df['start_year'].loc[df['credit_name'] == r.credit_name])}
                        OffCycleCredits._values[r.credit_name][r.start_year] = \
                            r.drop(['start_year', 'credit_name']).to_dict()

        return template_errors


if __name__ == '__main__':
    try:
        if '__file__' in locals():
            print(file_io.get_filenameext(__file__))

        import importlib
        from context.cost_clouds import CostCloud

        # set up global variables:
        omega_globals.options = OMEGASessionSettings()

        init_fail = []

        # pull in reg classes before building database tables (declaring classes) that check reg class validity
        module_name = get_template_name(omega_globals.options.policy_reg_classes_file)
        omega_globals.options.RegulatoryClasses = importlib.import_module(module_name).RegulatoryClasses
        init_fail += omega_globals.options.RegulatoryClasses.init_from_file(
            omega_globals.options.policy_reg_classes_file)

        init_omega_db(omega_globals.options.verbose)
        omega_log.init_logfile()

        SQABase.metadata.create_all(omega_globals.engine)

        init_fail += CostCloud.init_cost_clouds_from_file(omega_globals.options.vehicle_simulation_results_and_costs_file,
                                                          verbose=omega_globals.options.verbose)

        init_fail += OffCycleCredits.init_from_file(omega_globals.options.offcycle_credits_file,
                                                    verbose=omega_globals.options.verbose)

        if not init_fail:
            file_io.validate_folder(omega_globals.options.database_dump_folder)

            class dummyVehicle:
                model_year = 2020
                reg_class_id = 'car'
                cost_curve_class = 'ice_MPW_LRL'
                cost_cloud = CostCloud.get_cloud(model_year, cost_curve_class)

            vehicle = dummyVehicle()

            OffCycleCredits.calc_off_cycle_credits(vehicle)
        else:
            print(init_fail)
            print("\n#RUNTIME FAIL\n%s\n" % traceback.format_exc())
            os._exit(-1)
    except:
        print("\n#RUNTIME FAIL\n%s\n" % traceback.format_exc())
        os._exit(-1)
