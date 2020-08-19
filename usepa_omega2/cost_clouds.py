"""
cost_clouds.py
==============


"""

import o2  # import global variables
from usepa_omega2 import *

import cost_curves


class CostCloud(SQABase):
    # --- database table properties ---
    __tablename__ = 'cost_clouds'
    index = Column('index', Integer, primary_key=True)

    cost_curve_class = Column(String)
    model_year = Column(Numeric)
    new_vehicle_mfr_cost_dollars = Column(Float)
    cert_co2_grams_per_mile = Column(Float)
    mfr_deemed_new_vehicle_generalized_cost_dollars = Column(Float)

    def __repr__(self):
        return "<OMEGA2 %s object at 0x%x>" % (type(self).__name__, id(self))

    def __str__(self):
        s = ''  # '"<OMEGA2 %s object at 0x%x>" % (type(self).__name__,  id(self))
        for k in self.__dict__:
            s = s + k + ' = ' + str(self.__dict__[k]) + '\n'
        return s

    @staticmethod
    def init_database_from_file(filename, verbose=False):
        import matplotlib.pyplot as plt

        omega_log.logwrite('\nInitializing database from %s...' % filename)

        input_template_name = 'cost_clouds'
        input_template_version = 0.0003
        input_template_columns = {'cost_curve_class', 'model_year', 'cert_co2_grams_per_mile',
                                  'new_vehicle_mfr_cost_dollars'}

        template_errors = validate_template_version_info(filename, input_template_name, input_template_version,
                                                         verbose=verbose)

        if not template_errors:
            # read in the data portion of the input file
            df = pd.read_csv(filename, skiprows=1)

            template_errors = validate_template_columns(filename, input_template_columns, df.columns,
                                                        verbose=verbose)

            if not template_errors:
                obj_list = []
                # load cloud data into database
                for i in df.index:
                    obj_list.append(CostCloud(
                        cost_curve_class=df.loc[i, 'cost_curve_class'],
                        model_year=df.loc[i, 'model_year'],
                        new_vehicle_mfr_cost_dollars=df.loc[i, 'new_vehicle_mfr_cost_dollars'],
                        cert_co2_grams_per_mile=df.loc[i, 'cert_co2_grams_per_mile'],
                    ))
                o2.session.add_all(obj_list)
                original_echo = o2.engine.echo
                o2.engine.echo = False  # cloud has a lot of points... turn off echo
                if verbose:
                    print('\nAdding cost cloud to database...')
                o2.session.flush()
                o2.engine.echo = original_echo

            # convert cost clouds into curves and set up cost_curves table...
            cost_curve_classes = df['cost_curve_class'].unique()
            # for each cost curve class
            for cost_curve_class in cost_curve_classes:
                if verbose:
                    print(cost_curve_class)
                class_cloud = df[df['cost_curve_class'] == cost_curve_class]
                cloud_model_years = class_cloud['model_year'].unique()
                # for each model year
                for model_year in cloud_model_years:
                    if verbose:
                        print(model_year)
                    cloud = class_cloud[class_cloud['model_year'] == model_year]

                    # vars to hold column names
                    combined_GHG_gpmi = 'cert_co2_grams_per_mile'
                    combined_GHG_cost = 'new_vehicle_mfr_cost_dollars'

                    if verbose and model_year == cloud_model_years.min():
                        plt.figure()
                        plt.plot(cloud[combined_GHG_gpmi], cloud[combined_GHG_cost], '.')
                        plt.title('Cost versus CO2 %s' % cost_curve_class)
                        plt.xlabel('Combined GHG CO2 [g/mi]')
                        plt.ylabel('Combined GHG Cost [$]')
                        plt.grid()

                    # define frontier lists
                    min_co2_gpmi = []
                    min_co2_cost = []
                    # find frontier starting point, lowest GHGs, and add to frontier lists
                    min_co2_gpmi_index = cloud[combined_GHG_gpmi].idxmin()
                    min_co2_gpmi.append(cloud[combined_GHG_gpmi].loc[min_co2_gpmi_index])
                    min_co2_cost.append(cloud[combined_GHG_cost].loc[min_co2_gpmi_index])

                    # keep lower cost points
                    cloud = cloud[cloud[combined_GHG_cost] < min_co2_cost[-1]]
                    while len(cloud):
                        # calculate frontier factor (more negative is more better) = slope of each point relative
                        # to prior frontier point if frontier_social_affinity_factor = 1.0, else a "weighted" slope
                        cloud['frontier_factor'] = (cloud[combined_GHG_cost] - min_co2_cost[-1]) / (
                                cloud[combined_GHG_gpmi] - min_co2_gpmi[
                            -1]) ** o2.options.cost_curve_frontier_affinity_factor

                        # find next frontier point, lowest slope, and add to frontier lists
                        min_co2_gpmi_index = cloud['frontier_factor'].idxmin()
                        min_co2_gpmi.append(cloud[combined_GHG_gpmi].loc[min_co2_gpmi_index])
                        min_co2_cost.append(cloud[combined_GHG_cost].loc[min_co2_gpmi_index])

                        # keep lower cost points
                        cloud = cloud[cloud[combined_GHG_cost] < min_co2_cost[-1]]

                    if verbose and model_year == cloud_model_years.min():
                        plt.plot(min_co2_gpmi, min_co2_cost, 'r-')
                        plt.savefig(o2.options.output_folder + 'Cost versus CO2 %s' % cost_curve_class)
                    cost_curves.CostCurve.init_database_from_lists(cost_curve_class, model_year, min_co2_gpmi,
                                                                   min_co2_cost)

            plt.show()

        return template_errors

    def calculate_generalized_cost(self, cost_curve_class):
        print(cost_curve_class)


if __name__ == '__main__':
    if '__file__' in locals():
        print(fileio.get_filenameext(__file__))

    # set up global variables:
    o2.options = OMEGARuntimeOptions()
    init_omega_db()
    omega_log.init_logfile()
    o2.cost_file = 'input_templates/cost_clouds.csv'

    SQABase.metadata.create_all(o2.engine)

    init_fail = []
    init_fail = init_fail + CostCloud.init_database_from_file(o2.options.cost_file, verbose=o2.options.verbose)

    if not init_fail:
        dump_omega_db_to_csv(o2.options.database_dump_folder)
