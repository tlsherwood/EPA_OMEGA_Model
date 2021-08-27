"""

Compliance strategy implements the producer search algorithm to find a low-cost combination of technologies (via
vehicle CO2e g/mi) and market shares that achieve a targeted certification outcome.


----

**CODE**

"""


from omega_model import *
import numpy as np
import consumer

cache = dict()


def create_tech_and_share_sweeps(calendar_year, market_class_dict, candidate_production_decisions, share_range,
                                 consumer_response, node_name='', verbose=False):
    """
    Create tech and share sweeps is responsible for combining tech (CO2e g/mi levels) and market share options to
    develop a set of candidate compliance outcomes for the manufacturer in the given year as a function of the
    active policy.  The function recursively navigates the ``market_class_dict`` as a tree of market categories.

    Called from ``search_production_options()``.

    The combination of shares (to determine vehicle sales) and g/mi levels determines the CO2e Mg compliance outcome of
    each option outside of this function.

    On the first pass through this function, there are no ``candidate_production_decisions`` and there is not yet a
    ``consumer_response`` to those production decisions so the result of the first pass is effectively unconstrained
    (in the absence of required minimum production levels or production constraints).

    On the second pass, the producer has chosen one or more candidate production options from the prior cloud of
    choices, the share range is compressed based on the ``producer_compliance_search_convergence_factor`` setting.
    Subsequent tech options and market shares will be generated around the ``candidate_production_decisions``.

    Calls continue with subsequently tighter share ranges until the compliance target has been met within a tolerance.
    Ultimately a single candidate production decision is selected and passed to the consumer which reacts to the
    generalized cost of each option with a desired market share.

    If none of the outcomes are within the market share convergence tolerance then subsequent calls to this function
    include the ``consumer_response`` and are used as to generate nearby market share options, again as a function of
    the ``share_range`` as the producer continues to search the range of tech options.

    Args:
        calendar_year (int): the year in which the compliance calculations take place
        market_class_dict (dict): a dict of CompositeVehicle object lists hiearchically grouped by market categories
            into market classes
        candidate_production_decisions (None, DataFrame): zero or 1 or 2 candidate production decisions chosen from the
            results of the previous search iteration
        share_range (float): determines the numerical range of share and tech options that are considered
        consumer_response (Series): a pandas Series containing the final producer decision from prior iterations and
            containing the consumer desired market shares based on that decision and the producer's cross-subsidy, if
            any
        node_name (str): name of the node in the ``market_class_dict``, used to traverse the market class tree
        verbose (bool): enables additional console output if ``True``

    Returns:
        A dataframe containing a range of composite vehicle CO2e g/mi options factorially combined with market share
        options
         
    """
    child_df_list = []

    children = list(market_class_dict)

    # Generate tech options (CO2e g/mi levels)
    for k in market_class_dict:
        if verbose:
            print('processing ' + k)
        if type(market_class_dict[k]) is dict:
            # process subtree
            child_df_list.append(
                create_tech_and_share_sweeps(calendar_year, market_class_dict[k],
                                             candidate_production_decisions, share_range,
                                             consumer_response,
                                             node_name=k))
        else:
            # process leaf, loop over composite vehicles
            for cv in market_class_dict[k]:
                df = pd.DataFrame()

                if share_range == 1.0:
                    cv.tech_option_iteration_num = 0  # reset vehicle tech option progression

                if cv.fueling_class == 'ICE':
                    num_tech_options = omega_globals.options.producer_num_tech_options_per_ice_vehicle
                else:
                    num_tech_options = omega_globals.options.producer_num_tech_options_per_bev_vehicle

                veh_min_co2e_gpmi = cv.get_min_cert_co2e_gpmi()
                veh_max_co2e_gpmi = cv.get_max_cert_co2e_gpmi()

                if candidate_production_decisions is not None:
                    co2_gpmi_options = np.array([])
                    for idx, combo in candidate_production_decisions.iterrows():

                        if (combo['veh_%s_sales' % cv.vehicle_id] > 0) or (cv.tech_option_iteration_num > 0):
                            cv.tech_option_iteration_num += 1

                        tech_share_range = omega_globals.options.producer_compliance_search_convergence_factor ** \
                                           cv.tech_option_iteration_num
                        veh_co2e_gpmi = combo['veh_%s_co2e_gpmi' % cv.vehicle_id]
                        min_co2e_gpmi = max(veh_min_co2e_gpmi, veh_co2e_gpmi * (1 - tech_share_range))
                        max_co2e_gpmi = min(veh_max_co2e_gpmi, veh_co2e_gpmi * (1 + tech_share_range))
                        co2_gpmi_options = \
                            np.append(np.append(co2_gpmi_options,
                                      np.linspace(min_co2e_gpmi, max_co2e_gpmi, num=num_tech_options)), veh_co2e_gpmi)

                    if num_tech_options == 1:
                        co2_gpmi_options = [veh_max_co2e_gpmi]
                    else:
                        co2_gpmi_options = np.unique(co2_gpmi_options)  # filter out redundant tech options
                else:  # first producer pass, generate full range of options
                    if num_tech_options == 1:
                        co2_gpmi_options = [veh_max_co2e_gpmi]
                    else:
                        co2_gpmi_options = np.linspace(veh_min_co2e_gpmi, veh_max_co2e_gpmi, num=num_tech_options)

                tech_cost_options = cv.get_new_vehicle_mfr_cost_from_cost_curve(co2_gpmi_options)
                tech_generalized_cost_options = cv.get_new_vehicle_mfr_generalized_cost_from_cost_curve(co2_gpmi_options)
                tech_kwh_options = cv.get_cert_direct_kwh_pmi_from_cost_curve(co2_gpmi_options)

                df['veh_%s_co2e_gpmi' % cv.vehicle_id] = co2_gpmi_options
                df['veh_%s_kwh_pmi' % cv.vehicle_id] = tech_kwh_options
                df['veh_%s_cost_dollars' % cv.vehicle_id] = tech_cost_options
                df['veh_%s_generalized_cost_dollars' % cv.vehicle_id] = tech_generalized_cost_options

                child_df_list.append(df)

    # Generate market share options
    if consumer_response is None:
        # generate producer desired market shares for responsive market sectors
        producer_prefix = 'producer_share_frac_'
        if node_name:
            share_column_names = [producer_prefix + node_name + '.' + c for c in children]
        else:
            share_column_names = [producer_prefix + c for c in children]

        if all(s in omega_globals.options.MarketClass.responsive_market_categories for s in children):
            from context.production_constraints import ProductionConstraints
            from policy.required_sales_share import RequiredSalesShare

            min_constraints = dict()
            max_constraints = dict()
            for c in share_column_names:
                production_min = ProductionConstraints.get_minimum_share(calendar_year, c.replace(producer_prefix, ''))
                production_max = ProductionConstraints.get_maximum_share(calendar_year, c.replace(producer_prefix, ''))
                required_zev_share = RequiredSalesShare.get_minimum_share(calendar_year, c.replace(producer_prefix, ''))

                max_constraints[c] = production_max
                min_constraints[c] = min(production_max, max(required_zev_share, production_min))

            if share_range == 1.0:
                # span the whole space of shares
                sales_share_df = partition(share_column_names,
                                           num_levels=omega_globals.options.producer_num_market_share_options,
                                           min_constraints=min_constraints, max_constraints=max_constraints)
            else:
                # narrow search span to a range of shares around the winners
                from common.omega_functions import generate_constrained_nearby_shares
                sales_share_df = \
                    generate_constrained_nearby_shares(share_column_names, candidate_production_decisions,
                                                       share_range,
                                                       omega_globals.options.producer_num_market_share_options,
                                                       min_constraints=min_constraints,
                                                       max_constraints=max_constraints)
        else:
            sales_share_df = pd.DataFrame()
            for c, cn in zip(children, share_column_names):
                sales_share_df[cn] = [consumer.sales_volume.context_new_vehicle_sales(calendar_year)[c] /
                                      consumer.sales_volume.context_new_vehicle_sales(calendar_year)['total']]
    else:
        # inherit absolute market shares from consumer response
        if node_name:
            abs_share_column_names = ['producer_abs_share_frac_' + node_name + '.' + c for c in children]
        else:
            abs_share_column_names = ['producer_abs_share_frac_' + c for c in children]

        sales_share_df = pd.DataFrame()
        share_total = 0
        for cn in abs_share_column_names:
            if cn.replace('producer', 'consumer') in consumer_response:
                sales_share_df[cn] = [consumer_response[cn.replace('producer', 'consumer')]]
                share_total += sales_share_df[cn]

    # Combine tech and market share options
    if verbose:
        print('combining ' + str(children))
    tech_combos_df = pd.DataFrame()
    for df in child_df_list:
        tech_combos_df = cartesian_prod(tech_combos_df, df)

    if not sales_share_df.empty:
        tech_share_combos_df = cartesian_prod(tech_combos_df, sales_share_df)
    else:
        tech_share_combos_df = tech_combos_df

    return tech_share_combos_df


def apply_production_decision_to_composite_vehicles(composite_vehicles, selected_production_decision):
    """
    Apply the selected production decision to the given composite vehicles (g/mi results and sales) and decompose the
    composite values down to the source vehicles.  Update the composite vehicle CO2e Mg and cost values based on the
    weighted values of the source vehicles.

    Args:
        composite_vehicles (list): list of ``CompositeVehicle`` objects
        selected_production_decision (Series): the production decision as a result of the compliance search

    Returns:
        A list of updated `CompositeVehicle`` objects

    """
    import copy

    composite_vehicles = copy.deepcopy(composite_vehicles)
    from producer.vehicles import VehicleAttributeCalculations

    # assign co2 values and sales to vehicles...
    for cv in composite_vehicles:
        cv.cert_co2e_grams_per_mile = selected_production_decision['veh_%s_co2e_gpmi' % cv.vehicle_id]
        cv.cert_direct_kwh_per_mile = selected_production_decision['veh_%s_kwh_pmi' % cv.vehicle_id]
        cv.initial_registered_count = selected_production_decision['veh_%s_sales' % cv.vehicle_id]
        VehicleAttributeCalculations.perform_attribute_calculations(cv)
        cv.decompose()
        cv.new_vehicle_mfr_cost_dollars = \
            cv.get_weighted_attribute('new_vehicle_mfr_cost_dollars')
        cv.new_vehicle_mfr_generalized_cost_dollars = \
            cv.get_weighted_attribute('new_vehicle_mfr_generalized_cost_dollars')
        cv.cert_target_co2e_Mg = \
            cv.get_weighted_attribute('cert_target_co2e_Mg')
        cv.cert_co2e_Mg = \
            cv.get_weighted_attribute('cert_co2e_Mg')

    return composite_vehicles


def search_production_options(compliance_id, calendar_year, producer_decision_and_response,
                              producer_consumer_iteration_num, strategic_target_offset_Mg):
    """
    This function implements the producer search for a set of technologies (CO2e g/mi values) and market shares that
    achieve a desired compliance outcome taking into consideration the strategic target offset which allows
    intentional under- or over-compliance based on the producer's credit situation, for example.

    This function is called from ``omega.run_producer_consumer()``.

    On the first pass through, there is no ``producer_decision_and_response`` yet.  On subsequent iterations
    (``producer_consumer_iteration_num`` > 0) the producer decision and consumer response is used to constrain the range
    of market shares under consideration by the producer.

    Args:
        compliance_id (str): manufacturer name, or 'consolidated_OEM'
        calendar_year (int): the year of the compliance search
        producer_decision_and_response (Series): pandas Series containing the producer's selected production decision
            from the prior iteration and the consumer's desired market shares
        producer_consumer_iteration_num (int): the number of the producer-consumer iteration
        strategic_target_offset_Mg (float): if positive, the raw compliance outcome will be under-compliance, if
            negative then the raw compliance outcome will be over-compliance. Used to strategically under- or over-
            comply, perhaps as a result of the desired to earn or burn prior credits in the credit bank

    Returns:
        A tuple of ``composite_vehicles`` (list of CompositeVehicle objects),
        ``selected_production_decision`` (pandas Series containing the result of the serach),
        ``market_class_tree`` (dict of CompositeVehicle object lists hiearchically grouped by market categories
            into market classes), and ``producer_compliance_possible`` (bool that indicates whether compliance was
            achievable)

    """
    candidate_production_decisions = None
    producer_compliance_possible = False

    if (calendar_year == omega_globals.options.analysis_initial_year) and (producer_consumer_iteration_num == 0):
        cache.clear()

    producer_iteration_log = \
        omega_log.IterationLog('%s%d_%d_producer_iteration_log.csv' % (
            omega_globals.options.output_folder, calendar_year, producer_consumer_iteration_num))

    continue_search = True
    search_iteration = 0
    best_candidate_production_decision = None

    while continue_search:
        share_range = omega_globals.options.producer_compliance_search_convergence_factor ** search_iteration

        composite_vehicles, market_class_tree, context_based_total_sales = \
            create_composite_vehicles(calendar_year, compliance_id)

        tech_and_share_sweeps = create_tech_and_share_sweeps(calendar_year, market_class_tree,
                                                             candidate_production_decisions, share_range,
                                                             producer_decision_and_response)

        production_options = create_production_options(composite_vehicles, tech_and_share_sweeps,
                                                       context_based_total_sales)

        # insert code to cull production options based on policy here #

        production_options['share_range'] = share_range

        production_options['strategic_compliance_ratio'] = \
            (production_options['total_cert_co2e_megagrams'] - strategic_target_offset_Mg) / \
            np.maximum(1, production_options['total_target_co2e_megagrams'])

        production_options['strategic_target_offset_Mg'] = strategic_target_offset_Mg

        candidate_production_decisions, compliance_possible = \
            select_candidate_manufacturing_decisions(production_options, calendar_year, search_iteration,
                                                     producer_iteration_log, strategic_target_offset_Mg)

        producer_compliance_possible |= compliance_possible

        if (best_candidate_production_decision is None) or \
                (candidate_production_decisions['strategic_compliance_error'].min() <
                 best_candidate_production_decision['strategic_compliance_error'].min()):
            best_candidate_production_decision = \
                candidate_production_decisions.loc[candidate_production_decisions['strategic_compliance_error'].idxmin()]

        if 'producer' in omega_globals.options.verbose_console_modules:
            omega_log.logwrite(('%d_%d_%d' % (calendar_year, producer_consumer_iteration_num,
                                              search_iteration)).ljust(12) + 'SR:%f CR:%.10f' % (share_range,
                                    best_candidate_production_decision['strategic_compliance_ratio']), echo_console=True)

        search_iteration += 1

        continue_search = (abs(1 - best_candidate_production_decision['strategic_compliance_ratio']) > \
                           omega_globals.options.producer_compliance_search_tolerance) and \
                          (share_range > omega_globals.options.producer_compliance_search_min_share_range)

    if 'producer' in omega_globals.options.verbose_console_modules:
        omega_log.logwrite('PRODUCER FINAL COMPLIANCE DELTA %f' % abs(1 - best_candidate_production_decision['strategic_compliance_ratio']),
                           echo_console=True)

        omega_log.logwrite('Target GHG Offset Mg %.0f, Actual GHG Offset Mg %.0f' % (-best_candidate_production_decision['strategic_target_offset_Mg'], best_candidate_production_decision['total_credits_co2e_megagrams']),
                           echo_console=True)

        omega_log.logwrite('Target Compliance Ratio %3.3f, Actual Compliance Ratio %3.3f' %
                           ((best_candidate_production_decision['total_cert_co2e_megagrams']-best_candidate_production_decision['strategic_target_offset_Mg'])/max(1, best_candidate_production_decision['total_target_co2e_megagrams']),
                            best_candidate_production_decision['strategic_compliance_ratio']),
                           echo_console=True)

    selected_production_decision = pd.to_numeric(best_candidate_production_decision)

    selected_production_decision = \
        selected_production_decision.rename({'strategic_compliance_ratio': 'initial_strategic_compliance_ratio'})

    # log the final iteration, as opposed to the winning iteration:
    selected_production_decision['producer_search_iteration'] = search_iteration - 1

    if 'producer' in omega_globals.options.verbose_console_modules:
        for mc in omega_globals.options.MarketClass.market_classes:
            omega_log.logwrite(('%d producer_abs_share_frac_%s' % (calendar_year, mc)).ljust(50) + '= %s' %
                               (selected_production_decision['producer_abs_share_frac_%s' % mc]), echo_console=True)
        omega_log.logwrite('', echo_console=True)

    composite_vehicles = apply_production_decision_to_composite_vehicles(composite_vehicles,
                                                                         selected_production_decision)

    return composite_vehicles, selected_production_decision, market_class_tree, \
           producer_compliance_possible


def create_composite_vehicles(calendar_year, compliance_id):
    """
    Create composite vehicles based on the prior year's finalized vehicle production and update the sales mix based on
    projections from the context and caclulate this year's nominal sales for the compliance ID based on the context.

    Args:
        calendar_year (int): the year of the compliance search
        compliance_id (str): manufacturer name, or 'consolidated_OEM'

    Returns:
        tuple ``composite_vehicles`` (list of CompositeVehicle objects),
        ``market_class_tree`` (dict of CompositeVehicle object lists hiearchically grouped by market categories
        into market classes), ``context_based_total_sales`` (total vehicle sales based on the context for the given
        ``compliance_id``)

    """
    from producer.vehicles import VehicleFinal, Vehicle, CompositeVehicle, transfer_vehicle_data
    from consumer.sales_volume import context_new_vehicle_sales
    from context.new_vehicle_market import NewVehicleMarket

    cache_key = calendar_year
    if cache_key not in cache:
        # pull in last year's vehicles:
        manufacturer_prior_vehicles = VehicleFinal.get_compliance_vehicles(calendar_year - 1, compliance_id)

        Vehicle.reset_vehicle_ids()

        manufacturer_vehicles = []
        # update each vehicle and calculate compliance target for each vehicle
        for prior_veh in manufacturer_prior_vehicles:
            new_veh = Vehicle()
            transfer_vehicle_data(prior_veh, new_veh, model_year=calendar_year)
            manufacturer_vehicles.append(new_veh)
            new_veh.initial_registered_count = new_veh.base_year_market_share

        # sum([new_veh.base_year_market_share for new_veh in manufacturer_vehicles]) == 2.0 at this point due to
        # intentional duplicate entries for "alternative" powertrain vehicles, but "market_share" is used for relative
        # proportions

        context_based_total_sales = 0  # sales total by compliance id size class share
        for csc in NewVehicleMarket.context_size_classes: # for each context size class
            context_based_total_sales += \
                NewVehicleMarket.new_vehicle_sales(calendar_year, context_size_class=csc) \
                * VehicleFinal.mfr_base_year_size_class_share[compliance_id][csc]

        # calculate new vehicle absolute market share based on vehicle size mix from context
        for new_veh in manufacturer_vehicles:
            new_veh.base_year_market_share = \
                new_veh.initial_registered_count * \
                VehicleFinal.mfr_base_year_size_class_share[compliance_id][new_veh.context_size_class] / \
                context_based_total_sales

        # group by context size class
        csc_dict = dict()
        for new_veh in manufacturer_vehicles:
            if new_veh.context_size_class not in csc_dict:
                csc_dict[new_veh.context_size_class] = []
            csc_dict[new_veh.context_size_class].append(new_veh)

        # distribute context size class sales to manufacturer_vehicles by relative market share
        for csc in csc_dict: # for each context size class
            projection_initial_registered_count = \
                NewVehicleMarket.new_vehicle_sales(calendar_year, context_size_class=csc) \
                * VehicleFinal.mfr_base_year_size_class_share[compliance_id][csc]

            distribute_by_attribute(csc_dict[csc], projection_initial_registered_count,
                                    weight_by='base_year_market_share',
                                    distribute_to='initial_registered_count')

        # calculate new vehicle market share based on vehicle size mix from context
        for new_veh in manufacturer_vehicles:
            new_veh.base_year_market_share = new_veh.initial_registered_count / context_based_total_sales

        # sum([new_veh.base_year_market_share for new_veh in manufacturer_vehicles]) == 1.0 at this point,
        # sum([new_veh.initial_registered_count for new_veh in manufacturer_vehicles]) = context_based_total_sales

        # group by market class / reg class
        mctrc = dict()
        for mc in omega_globals.options.MarketClass.market_classes:
            mctrc[mc] = {'sales': 0}
            for rc in omega_globals.options.RegulatoryClasses.reg_classes:
                mctrc[mc][rc] = []
        for new_veh in manufacturer_vehicles:
            mctrc[new_veh.market_class_id][new_veh.reg_class_id].append(new_veh)
            mctrc[new_veh.market_class_id]['sales'] += new_veh.initial_registered_count

        composite_vehicles = []
        for mc in mctrc:
            for rc in omega_globals.options.RegulatoryClasses.reg_classes:
                if mctrc[mc][rc]:
                    cv = CompositeVehicle(mctrc[mc][rc], vehicle_id='%s.%s' % (mc, rc), weight_by='base_year_market_share')
                    cv.composite_vehicle_share_frac = cv.initial_registered_count / mctrc[mc]['sales']
                    composite_vehicles.append(cv)

        # get empty market class tree
        market_class_tree = omega_globals.options.MarketClass.get_market_class_tree()

        # populate tree with vehicle objects
        for new_veh in composite_vehicles:
            omega_globals.options.MarketClass.populate_market_classes(market_class_tree, new_veh.market_class_id, new_veh)

        cache[cache_key] = {'composite_vehicles': composite_vehicles,
                            'market_class_tree': market_class_tree,
                            'context_based_total_sales': context_based_total_sales}
    else:
        # pull cached composite vehicles (avoid recompute of composite frontiers, etc)
        composite_vehicles = cache[cache_key]['composite_vehicles']
        market_class_tree = cache[cache_key]['market_class_tree']
        context_based_total_sales = cache[cache_key]['context_based_total_sales']

    return composite_vehicles, market_class_tree, context_based_total_sales


def finalize_production(calendar_year, compliance_id, composite_vehicles, selected_production_decision):
    """
    Finalize vehicle production at the conclusion of the compliance search and producer-consumer market share
    iteration.  Source ``Vehicle`` objects from the composite vehicles are are converted to ``VehicleFinal`` objects
    and stored in the database.  Manufacturer Annual Data is updated with the certification results in CO2e Mg

    Args:
        calendar_year (int): the year of the compliance search
        compliance_id (str): manufacturer name, or 'consolidated_OEM'
        composite_vehicles (list): list of ``CompositeVehicle`` objects
        selected_production_decision (Series): the production decision as a result of the compliance search

    Returns:
        Nothing, updates the OMEGA database with the finalized vehicles

    """
    from producer.manufacturer_annual_data import ManufacturerAnnualData
    from producer.vehicles import VehicleFinal, transfer_vehicle_data

    manufacturer_new_vehicles = []

    # pull final vehicles from composite vehicles
    for cv in composite_vehicles:
        # update sales, which may have changed due to consumer response and iteration
        cv.initial_registered_count = selected_production_decision['veh_%s_sales' % cv.vehicle_id]
        if ((omega_globals.options.log_producer_iteration_years == 'all') or
            (calendar_year in omega_globals.options.log_producer_iteration_years)) and 'producer' in omega_globals.options.verbose_console_modules:
            cv.cost_curve.to_csv(omega_globals.options.output_folder + '%s_%s_cost_curve.csv' % (cv.model_year, cv.vehicle_id))
        cv.decompose()  # propagate sales to source vehicles
        for veh in cv.vehicle_list:
            # if 'producer' in o2.options.verbose_console:
            #     veh.cost_cloud.to_csv(o2.options.output_folder + '%s_%s_cost_cloud.csv' % (veh.model_year, veh.vehicle_id))
            veh_final = VehicleFinal()
            transfer_vehicle_data(veh, veh_final)
            manufacturer_new_vehicles.append(veh_final)

    omega_globals.session.add_all(manufacturer_new_vehicles)

    cert_target_co2e_Mg = VehicleFinal.calc_cert_target_co2e_Mg(calendar_year, compliance_id)

    cert_co2e_Mg = VehicleFinal.calc_cert_co2e_Mg(calendar_year, compliance_id)

    ManufacturerAnnualData. \
        create_manufacturer_annual_data(model_year=calendar_year,
                                        compliance_id=compliance_id,
                                        cert_target_co2e_Mg=cert_target_co2e_Mg,
                                        calendar_year_cert_co2e_Mg=cert_co2e_Mg,
                                        manufacturer_vehicle_cost_dollars=selected_production_decision['total_cost_dollars'],
                                        )
    omega_globals.session.flush()


def create_production_options(composite_vehicles, tech_and_share_combinations, total_sales):
    """
    Create a set of production options, including compliance outcomes, based on the given tech and share combinations.

    On the first time through, from the ``producer`` module, total_sales is based on context, market shares
    come from the producer desired market shares.

    On the second time through, from the ``omega`` module, total_sales is determined by sales response, market shares
    come from the consumer demanded market shares.

    Args:
        composite_vehicles (list): list of ``CompositeVehicle`` objects
        tech_and_share_combinations (DataFrame): the result of ``create_tech_and_share_sweeps()``
        total_sales (float): manufacturer total vehicle sales based on the context or the consumer response

    Returns:
        ``production_options`` DataFrame of technology and share options including compliance outcomes in CO2e Mg

    """
    production_options = tech_and_share_combinations

    total_target_co2e_Mg = 0
    total_cert_co2e_Mg = 0
    total_cost_dollars = 0
    total_generalized_cost_dollars = 0

    for composite_veh in composite_vehicles:
        # assign sales to vehicle based on market share fractions and reg class share fractions
        market_class = composite_veh.market_class_id

        if ('consumer_abs_share_frac_%s' % market_class) in production_options:
            composite_veh_sales = total_sales * production_options['consumer_abs_share_frac_%s' % market_class]

        elif ('producer_abs_share_frac_%s' % market_class) in production_options:
            composite_veh_sales = total_sales * production_options['producer_abs_share_frac_%s' % market_class]

        else:
            substrs = market_class.split('.')
            chain = []

            for i in range(len(substrs)):
                str = 'producer_share_frac_'
                for j in range(i + 1):
                    str = str + substrs[j] + '.' * (j != i)
                chain.append(str)

            composite_veh_sales = total_sales

            for c in chain:
                composite_veh_sales = composite_veh_sales * production_options[c]

            if ('producer_abs_share_frac_%s' % market_class) not in production_options:
                production_options['producer_abs_share_frac_%s' % market_class] = composite_veh_sales / total_sales
            else:
                production_options['producer_abs_share_frac_%s' % market_class] += composite_veh_sales / total_sales

        composite_veh_sales = composite_veh_sales * composite_veh.composite_vehicle_share_frac
        production_options['veh_%s_sales' % composite_veh.vehicle_id] = composite_veh_sales

        # calculate vehicle total cost
        composite_veh_total_cost_dollars = composite_veh_sales * \
                                           production_options['veh_%s_cost_dollars' % composite_veh.vehicle_id]

        production_options['veh_%s_total_cost_dollars' % composite_veh.vehicle_id] = composite_veh_total_cost_dollars

        composite_veh_total_generalized_cost_dollars = composite_veh_sales * \
                                                       production_options['veh_%s_generalized_cost_dollars' %
                                                                          composite_veh.vehicle_id]

        # calculate cert and target Mg for the vehicle
        composite_veh_cert_co2_gpmi = production_options['veh_%s_co2e_gpmi' % composite_veh.vehicle_id]

        composite_veh_cert_co2e_Mg = composite_veh.normalized_cert_co2e_Mg * composite_veh_cert_co2_gpmi * \
                                     composite_veh_sales

        composite_veh_target_co2e_Mg = composite_veh.normalized_cert_target_co2e_Mg * composite_veh_sales

        production_options['veh_%s_cert_co2e_megagrams' % composite_veh.vehicle_id] = composite_veh_cert_co2e_Mg
        production_options['veh_%s_target_co2e_megagrams' % composite_veh.vehicle_id] = composite_veh_target_co2e_Mg

        # update totals
        total_target_co2e_Mg += composite_veh_target_co2e_Mg
        total_cert_co2e_Mg += composite_veh_cert_co2e_Mg
        total_cost_dollars += composite_veh_total_cost_dollars
        total_generalized_cost_dollars += composite_veh_total_generalized_cost_dollars

    production_options['total_target_co2e_megagrams'] = total_target_co2e_Mg
    production_options['total_cert_co2e_megagrams'] = total_cert_co2e_Mg
    production_options['total_cost_dollars'] = total_cost_dollars
    production_options['total_generalized_cost_dollars'] = total_generalized_cost_dollars
    production_options['total_credits_co2e_megagrams'] = total_target_co2e_Mg - total_cert_co2e_Mg
    production_options['total_sales'] = total_sales

    return production_options


def plot_tech_share_combos_total(calendar_year, tech_share_combos_total):
    """

    Args:
        calendar_year:
        tech_share_combos_total:

    """
    import matplotlib.pyplot as plt
    plt.figure()
    plt.plot(tech_share_combos_total['total_cert_co2e_megagrams'],
             tech_share_combos_total['total_cost_dollars'], '.')
    plt.plot(tech_share_combos_total['total_target_co2e_megagrams'],
             tech_share_combos_total['total_cost_dollars'], 'r.')
    plt.xlabel('CO2e WITHOUT Offset [Mg]')
    plt.ylabel('Cost [$]')
    plt.title('%s' % calendar_year)
    plt.grid()

    plt.figure()
    plt.plot(tech_share_combos_total['total_cert_co2e_megagrams'] - tech_share_combos_total['strategic_target_offset_Mg'],
             tech_share_combos_total['total_cost_dollars'], '.')
    plt.plot(tech_share_combos_total['total_target_co2e_megagrams'],
             tech_share_combos_total['total_cost_dollars'], 'r.')
    plt.xlabel('CO2e WITH Offset [Mg]')
    plt.ylabel('Cost [$]')
    plt.title('%s' % calendar_year)
    plt.grid()

    plt.figure()
    plt.plot(tech_share_combos_total['strategic_compliance_ratio'],
             tech_share_combos_total['total_cost_dollars'], '.')
    plt.plot([1, 1], plt.ylim(), 'r')
    plt.xlabel('Compliance Ratio WITH Offset')
    plt.ylabel('Cost [$]')
    plt.title('%s' % calendar_year)
    plt.grid()

    plt.figure()
    plt.plot(tech_share_combos_total['strategic_compliance_ratio'],
             tech_share_combos_total['total_generalized_cost_dollars'], '.')
    plt.plot([1, 1], plt.ylim(), 'r')
    plt.xlabel('Compliance Ratio WITH Offset')
    plt.ylabel('Generalized Cost [$]')
    plt.title('%s' % calendar_year)
    plt.grid()

    plt.figure()
    plt.plot(tech_share_combos_total['strategic_compliance_ratio'],
             tech_share_combos_total['total_credits_co2e_megagrams'] +
             tech_share_combos_total['strategic_target_offset_Mg'], '.')
    plt.plot([1, 1], plt.ylim(), 'r')
    plt.xlabel('Compliance Ratio WITH Offset')
    plt.ylabel('Credits WITH Offset [Mg]')
    plt.title('%s' % calendar_year)
    plt.grid()


def select_candidate_manufacturing_decisions(tech_share_combos_total, calendar_year, search_iteration,
                                             producer_iteration_log, strategic_target_offset_Mg):
    """

    Args:
        tech_share_combos_total:
        calendar_year:
        search_iteration:
        producer_iteration_log:

    Returns:

    """
    # tech_share_combos_total = tech_share_combos_total.drop_duplicates('total_credits_co2e_megagrams')

    cost_name = 'total_generalized_cost_dollars'

    mini_df = pd.DataFrame()
    mini_df['total_credits_with_offset_co2e_megagrams'] = \
        tech_share_combos_total['total_credits_co2e_megagrams'] + strategic_target_offset_Mg
    mini_df['total_cost_dollars'] = tech_share_combos_total['total_cost_dollars']
    mini_df['total_generalized_cost_dollars'] = tech_share_combos_total['total_generalized_cost_dollars']
    mini_df['strategic_compliance_ratio'] = tech_share_combos_total['strategic_compliance_ratio']

    tech_share_combos_total['producer_search_iteration'] = search_iteration
    tech_share_combos_total['winner'] = False
    tech_share_combos_total['strategic_compliance_error'] = abs(1-tech_share_combos_total['strategic_compliance_ratio'])  # / tech_share_combos_total['total_generalized_cost_dollars']
    tech_share_combos_total['slope'] = 0

    compliant_tech_share_options = mini_df[(mini_df['total_credits_with_offset_co2e_megagrams']) >= 0].copy()
    non_compliant_tech_share_options = mini_df[(mini_df['total_credits_with_offset_co2e_megagrams']) < 0].copy()

    if not compliant_tech_share_options.empty and not non_compliant_tech_share_options.empty:
        # tech share options straddle compliance target
        compliance_possible = True

        # grab lowest-cost compliant option
        lowest_cost_compliant_tech_share_option = tech_share_combos_total.loc[[compliant_tech_share_options[cost_name].idxmin()]]

        # grab best non-compliant option
        non_compliant_tech_share_options['weighted_slope'] = \
            non_compliant_tech_share_options['strategic_compliance_ratio'] * \
            ((non_compliant_tech_share_options[cost_name] - float(lowest_cost_compliant_tech_share_option[cost_name])) /
            (non_compliant_tech_share_options['strategic_compliance_ratio'] - float(lowest_cost_compliant_tech_share_option['strategic_compliance_ratio'])))

        best_non_compliant_tech_share_option = tech_share_combos_total.loc[[non_compliant_tech_share_options['weighted_slope'].idxmin()]]

        if float(best_non_compliant_tech_share_option[cost_name]) > float(lowest_cost_compliant_tech_share_option[cost_name]):
            # cost cloud up-slopes from left to right, calculate slope relative to best non-compliant option
            compliant_tech_share_options['weighted_slope'] = \
                compliant_tech_share_options['strategic_compliance_ratio'] * \
                ((compliant_tech_share_options[cost_name] - float(best_non_compliant_tech_share_option[cost_name])) /
                (compliant_tech_share_options['strategic_compliance_ratio'] - float(best_non_compliant_tech_share_option['strategic_compliance_ratio'])))

            best_compliant_tech_share_option = tech_share_combos_total.loc[[compliant_tech_share_options['weighted_slope'].idxmax()]]
        else:
            best_compliant_tech_share_option = lowest_cost_compliant_tech_share_option

        winning_combos = pd.DataFrame.append(best_compliant_tech_share_option, best_non_compliant_tech_share_option)

    elif compliant_tech_share_options.empty:
        # grab best non-compliant option (least under-compliance)
        compliance_possible = False
        winning_combos = tech_share_combos_total.loc[[mini_df['total_credits_with_offset_co2e_megagrams'].idxmax()]]

    else: # non_compliant_tech_share_options.empty:
        # grab best compliant option (least over-compliant OR lowest cost?)
        compliance_possible = True
        # least over-compliant:
        winning_combos = tech_share_combos_total.loc[[mini_df['total_credits_with_offset_co2e_megagrams'].idxmin()]]
        # lowest cost:
        # winning_combos = tech_share_combos_total.loc[[[cost_name].idxmin()]]

    if (omega_globals.options.log_producer_iteration_years == 'all') or (calendar_year in omega_globals.options.log_producer_iteration_years):
        if 'producer' in omega_globals.options.verbose_console_modules:
            tech_share_combos_total.loc[winning_combos.index, 'winner'] = True
            if omega_globals.options.slice_tech_combo_cloud_tables:
                tech_share_combos_total = tech_share_combos_total[tech_share_combos_total['strategic_compliance_ratio'] <= 1.2]
            producer_iteration_log.write(tech_share_combos_total)
        else:
            winning_combos['winner'] = True
            producer_iteration_log.write(winning_combos)

    return winning_combos.copy(), compliance_possible


if __name__ == '__main__':
    try:
        if '__file__' in locals():
            print(file_io.get_filenameext(__file__))
    except:
        print("\n#RUNTIME FAIL\n%s\n" % traceback.format_exc())
        os._exit(-1)
