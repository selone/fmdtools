# -*- coding: utf-8 -*-
"""
Created on Tue Dec 21 08:52:58 2021

@author: dhulse
"""
import unittest
from examples.pump.pump_stochastic import Pump, PumpParam
from fmdtools.sim import propagate as prop
from fmdtools.sim.sample import ParameterSample, ParameterDomain
from tests.common import CommonTests
from fmdtools.analyze.common import suite_for_plots
from fmdtools.analyze.tabulate import NominalEnvelope
import numpy as np
import multiprocessing as mp


class StochasticPumpTests(unittest.TestCase, CommonTests):
    maxDiff = None

    def setUp(self):
        self.mdl = Pump()

    def test_stochastic_pdf(self):
        """Tests that (1) track_pdf option runs and (2) gives repeated 
        probability density results under the same seed(s)"""
        testvals = [23.427857638009993,
                    28.879844891816045,
                    0.0009482614961342181,
                    10.9180526929105,
                    0.02603536236159078,
                    1.9736111095116995,
                    31.579024323385077,
                    0.016549021807197088,
                    6.303651266980214]
        for i in range(1,10):
            self.mdl.update_seed(i)
            self.mdl.propagate(i, run_stochastic='track_pdf')
            pd = self.mdl.return_probdens()
            #print(pd)
            self.assertAlmostEqual(pd, testvals[i-1])

    def test_run_safety(self):
        """Test so models with the same seed will run the same/produce same results."""
        for seed in [1, 10, 209840]:
            mdl = Pump(r={'seed': seed})
            res_1, hist_1 = prop.nominal(mdl, run_stochastic=True, showprogress=False)
            res_f1, hist_f1 = prop.single_faults(mdl, run_stochastic=True,
                                                 showprogress=False)
            if seed == None:
                seed = mdl.r.seed
            mdl2 = Pump(r={'seed': seed})
            res_2,  hist_2 = prop.nominal(mdl2, run_stochastic=True, showprogress=False)
            res_f2, hist_f2 = prop.single_faults(mdl2, run_stochastic=True,
                                                showprogress=False)
            self.assertTrue(all(hist_1.fxns.move_water.s.eff ==
                            hist_2.fxns.move_water.s.eff))
            self.check_same_hist(hist_f1, hist_f2)

    def test_set_seeds(self):
        """Test that model seeds set with update_seed."""
        for seed in [1, 10, 209840]:
            mdl = Pump(r={'seed': seed})
            mdl2 = Pump()
            mdl2.update_seed(seed)
            self.assertEqual(seed, mdl.r.seed, mdl2.r.seed)

    def test_run_approach(self):
        """Test that random behaviors average out."""
        mdl = Pump()
        ps = ParameterSample()
        ps.add_variable_replicates([], replicates=1000)
        res, hist = prop.parameter_sample(mdl, ps, showprogress=False,
                                          run_stochastic=True,
                                          track={'fxns': {'move_water': "r"}},
                                          desired_result={})
        ave_effs = []
        std_effs = []
        for scen in ps.named_scenarios():
            ave_effs.append(np.mean(hist.get(scen).fxns.move_water.r.s.eff))
            std_effs.append(np.std(hist.get(scen).fxns.move_water.r.s.eff))
        ave_eff = np.mean(ave_effs)
        std_eff = np.mean(std_effs)
        # test means
        self.assertAlmostEqual(ave_eff, mdl.fxns['move_water'].r.s.eff_update[1][0], 2)
        self.assertLess(abs(std_eff-mdl.fxns['move_water'].r.s.eff_update[1][1]), 0.05)

    def test_model_copy_same(self):
        self.check_model_copy_same(Pump(), Pump(), [10, 20, 30], 25,
                                   max_time=55, run_stochastic=True)

    def test_model_copy_different(self):
        self.check_model_copy_different(Pump(), [10, 20, 30],
                                        max_time=55, run_stochastic=True)

    def test_model_reset(self):
        mdl = Pump()
        mdl2 = Pump()
        mdl2.r.seed = mdl.r.seed
        self.check_model_reset(mdl, mdl2, [10, 20, 30],
                               max_time=55, run_stochastic=True)

    def test_param_sample_save(self):
        ps = ParameterSample()
        ps.add_variable_replicates([], replicates=10)
        self.check_ps_save(self.mdl, ps, "stochpump_res.pkl", "spump_hist.pkl",
                           run_stochastic=True, pool=mp.Pool(4))
        self.check_ps_save(self.mdl, ps, "stochpump_res.csv", "spump_hist.csv",
                           run_stochastic=True, pool=mp.Pool(4))
        self.check_ps_save(self.mdl, ps, "stochpump_res.json", "spump_hist.json",
                           run_stochastic=True, pool=mp.Pool(4))

    def test_param_sample_isave(self):
        ps = ParameterSample()
        ps.add_variable_replicates([], replicates=10)
        fnames = ("spump_res", "spump_hist")
        self.check_ps_isave(self.mdl, ps, *fnames, "pkl", run_stochastic=True, pool=mp.Pool(4))
        self.check_ps_isave(self.mdl, ps, *fnames, "csv", run_stochastic=True, pool=mp.Pool(4))
        self.check_ps_isave(self.mdl, ps, *fnames, "json", run_stochastic=True, pool=mp.Pool(4))

    def test_nested_sample_save(self):
        ps = ParameterSample()
        ps.add_variable_replicates([], replicates=10)
        faultdomains = {'fd': (('all', ), {})}
        faultsamples = {'fs': (('fault_phases', 'fd'), {})}
        self.check_ns_save(self.mdl, ps, faultdomains, faultsamples, "spump_res.pkl", "spump_hist.pkl", run_stochastic=True, pool=mp.Pool(4))
        self.check_ns_save(self.mdl, ps, faultdomains, faultsamples, "spump_res.csv", "spump_hist.csv", run_stochastic=True, pool=mp.Pool(4))
        self.check_ns_save(self.mdl, ps, faultdomains, faultsamples, "spump_res.json", "spump_hist.json", run_stochastic=True, pool=mp.Pool(4))

    def test_nested_sample_isave(self):
        ps = ParameterSample()
        ps.add_variable_replicates([], replicates=10)
        faultdomains = {'fd': (('all', ), {})}
        faultsamples = {'fs': (('fault_phases', 'fd'), {})}
        fnames = ("spump_res", "spump_hist")
        self.check_ns_isave(self.mdl, ps, faultdomains, faultsamples, *fnames, "pkl", run_stochastic=True, pool=mp.Pool(4))
        self.check_ns_isave(self.mdl, ps, faultdomains, faultsamples, *fnames, "csv", run_stochastic=True, pool=mp.Pool(4))
        self.check_ns_isave(self.mdl, ps, faultdomains, faultsamples, *fnames, "json", run_stochastic=True, pool=mp.Pool(4))

    def test_plot_nominal_vals(self):
        """tests nominal_vals_1d"""
        mdl = Pump()
        ps = ParameterSample()
        ps.add_variable_replicates([], replicates=10)
        res, hist = prop.parameter_sample(mdl, ps, run_stochastic=True,
                                          showprogress=False)
        res['rep0_var_0.endclass.cost'] = 10.0
        # an.plot.nominal_vals_1d(app, endres, 'r.seed', metric="nonsense")
        title = "should show at least one red line over range of seeds"

        ne = NominalEnvelope(ps, res, 'cost', 'r.seed')
        ne.as_plot(title=title, f_kwargs={'alpha': 1.0})


    def test_plot_nominal_vals_xd(self):
        """tests nominal_vals_2d and nominal_vals_3d"""
        mdl = Pump()

        pd = ParameterDomain(PumpParam)
        pd.add_variable("delay")

        ps2 = ParameterSample(pd)
        ps2.add_variable_replicates([[0]], replicates=100, name="nodelay")
        ps2.add_variable_replicates([[10]], replicates=100, name="delay10")
        ps2.add_variable_replicates([[15]], replicates=100, name="delay15")
        nomres, nomhist = prop.parameter_sample(mdl, ps2,
                                                showprogress=False)

        res, hist = prop.parameter_sample(mdl, ps2, run_stochastic=True,
                                          showprogress=False)
        res['delay_10_20.endclass.cost'] = 10.0
        title = ("should show at least one red x over range of seeds," +
                 " probs, and delay={1, 10}")
        f_kwargs = {'alpha': 1.0}
        n_kwargs = {'alpha': 0.01}
        ne1 = NominalEnvelope(ps2, res, 'cost', 'r.seed', 'p.delay')
        a=1
        ne1.as_plot(title=title, f_kwargs=f_kwargs, n_kwargs=n_kwargs)

        ne2 = NominalEnvelope(ps2, res, 'cost', 'r.seed', 'p.delay', 'prob')
        ne2.as_plot(title=title, f_kwargs=f_kwargs, n_kwargs=n_kwargs)

    def test_plot_nested_hists(self):
        """Qualitative test to show that distributions carry over to fault scenarios
        in a nested approach."""
        mdl = Pump()
        pd = ParameterDomain(PumpParam)
        pd.add_variable("delay")

        ps = ParameterSample(pd)
        ps.add_variable_replicates([[5]], replicates=10, name="delay5")
        ps.add_variable_replicates([[15]], replicates=10, name="delay15")

        faultdomains = {'fd': (('fault', 'export_water', 'block'), {})}
        faultsamples = {'fs': (('fault_phases', 'fd'), {})}

        ecs, hists, apps = prop.nested_sample(mdl, ps, run_stochastic=True,
                                              showprogress=False,
                                              faultdomains=faultdomains,
                                              faultsamples=faultsamples,
                                              pool=mp.Pool(4))

        # test plot groups (and make sure behavior is different/expected in faults):
        comp_mdlhists = hists.get_scens('export_water_block_t27p0')
        comp_groups = {'delay_5': ps.get_scens(p={'delay': 5}),
                       'delay_15': ps.get_scens(p={'delay': 15})}
        title = "should show stochastic behavior in two groups"
        comp_mdlhists.plot_line('fxns.move_water.s.eff',
                                'fxns.move_water.s.total_flow',
                                'flows.wat_2.s.flowrate',
                                'flows.wat_2.s.pressure',
                                comp_groups=comp_groups,
                                aggregation='percentile',
                                time_slice=27,
                                title=title)
        # test metric dist
        title = "should show three groups for total_flow but one for eff"
        comp_mdlhists.plot_metric_dist([5, 10, 15],
                                       'fxns.move_water.s.eff',
                                       'fxns.move_water.s.total_flow',
                                       'flows.wat_2.s.flowrate',
                                       'flows.wat_2.s.pressure',
                                       title=title, alpha=0.5)

    def test_rand_paramsample_plot(self):
        ps = ParameterSample()
        ps.add_variable_replicates([], 20)
        mdl = Pump()
        res, hist = prop.parameter_sample(mdl, ps, run_stochastic=True,
                                          showprogress=False)

        title = "should show bounds and perc of random variables over time"
        hist.plot_line('move_water.r.s.eff', 'move_water.s.total_flow',
                       'wat_2.s.flowrate', 'wat_2.s.pressure',
                       'import_ee.r.s.effstate', 'import_ee.r.s.grid_noise',
                       'ee_1.s.voltage', 'sig_1.s.power',
                       color='blue', comp_groups={}, aggregation='percentile',
                       title=title)

        title = 'should show mean and ci of random variables over time'
        hist.plot_line('move_water.r.s.eff', 'move_water.s.total_flow',
                       'wat_2.s.flowrate', 'wat_2.s.pressure',
                       'import_ee.r.s.effstate', 'import_ee.r.s.grid_noise',
                       'ee_1.s.voltage', 'sig_1.s.power',
                       color='blue', comp_groups={}, aggregation='mean_ci',
                       title=title)

    def test_mdl_pickle(self):
        from fmdtools.define.block import SimParam
        from fmdtools.define.model import check_model_pickleability
        sp = SimParam(phases=(('start', 0, 4), ('on', 5, 49), ('end', 50, 55)),
                      times=(0, 20, 55), dt=1.0, units='hr')
        mdl = Pump(r={'seed': 5}, sp=sp)
        check_model_pickleability(mdl, try_pick=True)

    def test_model_set_vars(self):
        """Test that vars are set to using set_vars."""
        mdl = Pump()
        mdl.set_vars([['ee_1', 's', 'current']], [3.0])
        self.assertEqual(mdl.flows['ee_1'].s.current, 3.0)


if __name__ == '__main__':
    # suite = unittest.TestSuite()
    # suite.addTest(StochasticPumpTests("test_plot_nominal_vals_xd"))
    # suite.addTest(StochasticPumpTests("test_run_approach"))

    # suite.addTest(StochasticPumpTests("test_save_load_nominalapproach"))
    # suite.addTest(StochasticPumpTests("test_save_load_nominalapproach_indiv"))
    # runner = unittest.TextTestRunner()
    # runner.run(suite)
    # runner = unittest.TextTestRunner()
    # runner.run(suite_for_plots(StochasticPumpTests))

    # runner = unittest.TextTestRunner()
    # runner.run(suite_for_plots(StochasticPumpTests, True))
    unittest.main()
