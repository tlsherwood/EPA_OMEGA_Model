"""

**Loads parameters and provides calculations for an attribute-based (vehicle footprint) GHG standard.**

This is based on the current standards, with two regulatory classes with lifetime VMT and
parameter-based target calculations that define a "footprint curve" based on four coefficients
("A" through "D") and min and max footprint limits.


----

**CODE**

"""

print('importing %s' % __file__)

from usepa_omega2 import *

input_template_name = 'ghg_standards-footprint'

cache = dict()


class GHGStandardFootprint(SQABase, OMEGABase):
    """

    """
    # --- database table properties ---
    __tablename__ = 'ghg_standards_footprint'
    index = Column(Integer, primary_key=True)  #: database index
    model_year = Column(Numeric)  #: model year (or start year of the applied parameters)
    reg_class_ID = Column('reg_class_id', Enum(*reg_classes, validate_strings=True))  #: reg class name, e.g. 'car','truck'
    footprint_min_sqft = Column('footprint_min_sqft', Float)  #: minimum footprint (square feet) of curve
    footprint_max_sqft = Column('footprint_max_sqft', Float)  #: maximum footprint (square feet) of curve
    coeff_a = Column('coeff_a', Float)  #: footprint curve A coefficient
    coeff_b = Column('coeff_b', Float)  #: footprint curve B coefficient
    coeff_c = Column('coeff_c', Float)  #: footprint curve C coefficient
    coeff_d = Column('coeff_d', Float)  #: footprint curve D coefficient
    lifetime_VMT = Column('lifetime_vmt', Float)  #: regulatory lifetime VMT (in miles) of the given reg class

    @staticmethod
    def get_vehicle_reg_class(vehicle):
        """
        Get vehicle regulatory class based on vehicle characteristics.

        Args:
            vehicle (VehicleFinal): the vehicle to determine the reg class of

        Returns:

            Vehicle reg class based on vehicle characteristics.

        """
        reg_class_ID = vehicle.reg_class_ID
        return reg_class_ID

    @staticmethod
    def calc_target_co2_gpmi(vehicle):
        """
        Calculate vehicle target CO2 g/mi.

        Args:
            vehicle (Vehicle): the vehicle to get the target for

        Returns:

            Vehicle target CO2 in g/mi.

        """
        start_years = cache[vehicle.reg_class_ID]['start_year']
        vehicle_model_year = max(start_years[start_years <= vehicle.model_year])

        cache_key = '%s_%s_coefficients' % (vehicle_model_year, vehicle.reg_class_ID)
        if cache_key not in cache:
            cache[cache_key] = o2.session.query(GHGStandardFootprint). \
                filter(GHGStandardFootprint.reg_class_ID == vehicle.reg_class_ID). \
                filter(GHGStandardFootprint.model_year == vehicle_model_year).one()
        coefficients = cache[cache_key]

        if vehicle.footprint_ft2 <= coefficients.footprint_min_sqft:
            target_co2_gpmi = coefficients.coeff_a
        elif vehicle.footprint_ft2 > coefficients.footprint_max_sqft:
            target_co2_gpmi = coefficients.coeff_b
        else:
            target_co2_gpmi = vehicle.footprint_ft2 * coefficients.coeff_c + coefficients.coeff_d

        return target_co2_gpmi

    @staticmethod
    def calc_cert_lifetime_vmt(reg_class_id, model_year):
        """
        Get lifetime VMT as a function of regulatory class and model year.

        Args:
            reg_class_id (str): e.g. 'car','truck'
            model_year (numeric): model year

        Returns:

            Lifetime VMT for the regulatory class and model year.

        """
        start_years = cache[reg_class_id]['start_year']
        model_year = max(start_years[start_years <= model_year])

        cache_key = '%s_%s_lifetime_vmt' % (model_year, reg_class_id)
        if cache_key not in cache:
            cache[cache_key] = o2.session.query(GHGStandardFootprint.lifetime_VMT). \
                filter(GHGStandardFootprint.reg_class_ID == reg_class_id). \
                filter(GHGStandardFootprint.model_year == model_year).scalar()
        return cache[cache_key]

    @staticmethod
    def calc_target_co2_Mg(vehicle, sales_variants=None):
        """
        Calculate vehicle target CO2 Mg as a function of the vehicle, the standards and optional sales options.

        Includes the effect of production multipliers.

        See Also:

            GHG_standards_incentives.GHGStandardIncentives

        Args:
            vehicle (Vehicle): the vehicle
            sales_variants (numeric list-like): optional sales variants

        Returns:

            Target CO2 Mg value(s) for the given vehicle and/or sales variants.

        """
        import numpy as np
        from GHG_standards_incentives import GHGStandardIncentives

        start_years = cache[vehicle.reg_class_ID]['start_year']
        vehicle_model_year = max(start_years[start_years <= vehicle.model_year])

        lifetime_VMT = GHGStandardFootprint.calc_cert_lifetime_vmt(vehicle.reg_class_ID, vehicle_model_year)

        co2_gpmi = GHGStandardFootprint.calc_target_co2_gpmi(vehicle)

        if sales_variants is not None:
            if not (type(sales_variants) == pd.Series) or (type(sales_variants) == np.ndarray):
                sales = np.array(sales_variants)
            else:
                sales = sales_variants
        else:
            sales = vehicle.initial_registered_count

        return co2_gpmi * lifetime_VMT * sales * GHGStandardIncentives.get_production_multiplier(vehicle) / 1e6

    @staticmethod
    def calc_cert_co2_Mg(vehicle, co2_gpmi_variants=None, sales_variants=[1]):
        """
        Calculate vehicle cert CO2 Mg as a function of the vehicle, the standards, CO2 g/mi options and optional sales
        options.

        Includes the effect of production multipliers.

        See Also:

            GHG_standards_incentives.GHGStandardIncentives

        Args:
            vehicle (Vehicle): the vehicle
            sales_variants (numeric list-like): optional sales variants

        Returns:

            Cert CO2 Mg value(s) for the given vehicle, CO2 g/mi variants and/or sales variants.

        """
        import numpy as np
        from GHG_standards_incentives import GHGStandardIncentives

        start_years = cache[vehicle.reg_class_ID]['start_year']
        vehicle_model_year = max(start_years[start_years <= vehicle.model_year])

        lifetime_VMT = GHGStandardFootprint.calc_cert_lifetime_vmt(vehicle.reg_class_ID, vehicle_model_year)

        if co2_gpmi_variants is not None:
            if not (type(sales_variants) == pd.Series) or (type(sales_variants) == np.ndarray):
                sales = np.array(sales_variants)
            else:
                sales = sales_variants

            if not (type(co2_gpmi_variants) == pd.Series) or (type(co2_gpmi_variants) == np.ndarray):
                co2_gpmi = np.array(co2_gpmi_variants)
            else:
                co2_gpmi = co2_gpmi_variants
        else:
            sales = vehicle.initial_registered_count
            co2_gpmi = vehicle.cert_co2_grams_per_mile

        return co2_gpmi * lifetime_VMT * sales * GHGStandardIncentives.get_production_multiplier(vehicle) / 1e6

    @staticmethod
    def init_database_from_file(filename, verbose=False):
        """

        Initialize class data from input file.

        Args:
            filename (str): name of input file
            verbose (bool): enable additional console and logfile output if True

        Returns:
            List of template/input errors, else empty list on success

        """
        import numpy as np

        cache.clear()

        if verbose:
            omega_log.logwrite('\nInitializing database from %s...' % filename)

        input_template_version = 0.1
        input_template_columns = {'start_year', 'reg_class_id', 'fp_min', 'fp_max', 'a_coeff', 'b_coeff', 'c_coeff',
                                  'd_coeff', 'lifetime_vmt'}

        template_errors = validate_template_version_info(filename, input_template_name, input_template_version,
                                                         verbose=verbose)

        if not template_errors:
            # read in the data portion of the input file
            df = pd.read_csv(filename, skiprows=1)

            template_errors = validate_template_columns(filename, input_template_columns, df.columns, verbose=verbose)

            if not template_errors:
                obj_list = []
                # load data into database
                for i in df.index:
                    obj_list.append(GHGStandardFootprint(
                        model_year=df.loc[i, 'start_year'],
                        reg_class_ID=df.loc[i, 'reg_class_id'],
                        footprint_min_sqft=df.loc[i, 'fp_min'],
                        footprint_max_sqft=df.loc[i, 'fp_max'],
                        coeff_a=df.loc[i, 'a_coeff'],
                        coeff_b=df.loc[i, 'b_coeff'],
                        coeff_c=df.loc[i, 'c_coeff'],
                        coeff_d=df.loc[i, 'd_coeff'],
                        lifetime_VMT=df.loc[i, 'lifetime_vmt'],
                    ))
                o2.session.add_all(obj_list)
                o2.session.flush()

                for rc in df['reg_class_id'].unique():
                    cache[rc] = {'start_year': np.array(df['start_year'].loc[df['reg_class_id'] == rc])}

        return template_errors


if __name__ == '__main__':
    try:
        if '__file__' in locals():
            print(fileio.get_filenameext(__file__))

        # set up global variables:
        o2.options = OMEGARuntimeOptions()
        o2.options.ghg_standards_file = os.path.dirname(os.path.abspath(__file__)) + os.sep + 'test_inputs/ghg_standards-footprint.csv'
        init_omega_db()
        omega_log.init_logfile()

        SQABase.metadata.create_all(o2.engine)

        init_fail = []
        init_fail += GHGStandardFootprint.init_database_from_file(o2.options.ghg_standards_file,
                                                                             verbose=o2.options.verbose)

        if not init_fail:
            dump_omega_db_to_csv(o2.options.database_dump_folder)

            o2.options.GHG_standard = GHGStandardFootprint


            class dummyVehicle:
                model_year = None
                reg_class_ID = None
                footprint_ft2 = None
                initial_registered_count = None

                def get_initial_registered_count(self):
                    return self.initial_registered_count


            car_vehicle = dummyVehicle()
            car_vehicle.model_year = 2021
            car_vehicle.reg_class_ID = reg_classes.car
            car_vehicle.footprint_ft2 = 41
            car_vehicle.initial_registered_count = 1

            truck_vehicle = dummyVehicle()
            truck_vehicle.model_year = 2021
            truck_vehicle.reg_class_ID = reg_classes.truck
            truck_vehicle.footprint_ft2 = 41
            truck_vehicle.initial_registered_count = 1

            car_target_co2_gpmi = o2.options.GHG_standard.calc_target_co2_gpmi(car_vehicle)
            car_target_co2_Mg = o2.options.GHG_standard.calc_target_co2_Mg(car_vehicle)
            car_certs_co2_Mg = o2.options.GHG_standard.calc_cert_co2_Mg(car_vehicle,
                                                                             co2_gpmi_variants=[0, 50, 100, 150])
            car_certs_sales_co2_Mg = o2.options.GHG_standard.calc_cert_co2_Mg(car_vehicle,
                                                                                   co2_gpmi_variants=[0, 50, 100, 150],
                                                                                   sales_variants=[1, 2, 3, 4])

            truck_target_co2_gpmi = o2.options.GHG_standard.calc_target_co2_gpmi(truck_vehicle)
            truck_target_co2_Mg = o2.options.GHG_standard.calc_target_co2_Mg(truck_vehicle)
            truck_certs_co2_Mg = o2.options.GHG_standard.calc_cert_co2_Mg(truck_vehicle, [0, 50, 100, 150])
            truck_certs_sales_co2_Mg = o2.options.GHG_standard.calc_cert_co2_Mg(truck_vehicle, [0, 50, 100, 150],
                                                                                     sales_variants=[1, 2, 3, 4])
        else:
            print(init_fail)
            print("\n#RUNTIME FAIL\n%s\n" % traceback.format_exc())
            os._exit(-1)
    except:
        print("\n#RUNTIME FAIL\n%s\n" % traceback.format_exc())
        os._exit(-1)