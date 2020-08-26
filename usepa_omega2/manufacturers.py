"""
manufacturers.py
================


"""

import o2  # import global variables
from usepa_omega2 import *


class Manufacturer(SQABase):
    # --- database table properties ---
    __tablename__ = 'manufacturers'
    manufacturer_ID = Column('manufacturer_id', String, primary_key=True)
    vehicles = relationship('Vehicle', back_populates='manufacturer')

    # --- static properties ---

    def __repr__(self):
        return "<OMEGA2 %s object at 0x%x>" % (type(self).__name__,  id(self))

    def __str__(self):
        s = '\n<manufacturer.Manufacturer object at %#x>\n' % id(self)
        for k in self.__dict__:
            s = s + k + ' = ' + str(self.__dict__[k]) + '\n'
        return s

    @staticmethod
    def init_database_from_file(filename, verbose=False):
        if verbose:
            omega_log.logwrite('\nInitializing database from %s...' % filename)

        input_template_name = 'manufacturers'
        input_template_version = 0.0003
        input_template_columns = {'manufacturer_id'}

        template_errors = validate_template_version_info(filename, input_template_name, input_template_version, verbose=verbose)

        if not template_errors:
            # read in the data portion of the input file
            df = pd.read_csv(filename, skiprows=1)

            template_errors = validate_template_columns(filename, input_template_columns, df.columns, verbose=verbose)

            if not template_errors:
                obj_list = []
                # load data into database
                for i in df.index:
                    obj_list.append(Manufacturer(
                        manufacturer_ID=df.loc[i, 'manufacturer_id'],
                    ))
                o2.session.add_all(obj_list)
                o2.session.flush()

        return template_errors


if __name__ == '__main__':
    if '__file__' in locals():
        print(fileio.get_filenameext(__file__))

    # set up global variables:
    o2.options = OMEGARuntimeOptions()
    init_omega_db()

    from fuels import Fuel
    from market_classes import MarketClass
    from vehicles import Vehicle

    SQABase.metadata.create_all(o2.engine)

    init_fail = []
    init_fail = init_fail + Manufacturer.init_database_from_file(o2.options.manufacturers_file, verbose=o2.options.verbose)

    if not init_fail:
        dump_omega_db_to_csv(o2.options.database_dump_folder)
