# -*- coding: utf-8 -*-
"""
Created on Mon Dec 20 15:49:13 2021

@author: dhulse
"""
import os
import unittest
from examples.pump.ex_pump import Pump
from fmdtools.sim import propagate as prop
import fmdtools.analyze as an
from fmdtools.define.common import check_pickleability
from fmdtools.sim.sample import FaultDomain, FaultSample, ParameterSample
from tests.common import CommonTests
import numpy as np
from fmdtools.analyze.result import load
from fmdtools.analyze.history import History


class PumpTests(unittest.TestCase, CommonTests):
    """Overall test structure for Pump model"""

    def setUp(self):
        self.default_mdl = Pump()
        self.mdl = Pump()
        self.water_mdl = Pump(p={'cost': ('water',), 'delay': 10})
        self.fd = FaultDomain(self.mdl)
        self.fd.add_all()
        self.fs = FaultSample(self.fd)
        self.fs.add_fault_phases()
        self.faultdomains = {'fd': (('all', ), {})}
        self.faultsamples = {'fs': (('fault_phases', 'fd'), {})}
        self.ps = ParameterSample()
        self.ps.add_variable_replicates([], replicates=10)
        self.filenames = ("pump_res", "pump_hist")

    def test_value_setting(self):
        statenames = ['sig_1.s.power', 'move_water.s.eff']
        newvalues = [20, 0.1]
        self.check_var_setting(self.mdl, statenames, newvalues)

    def test_value_setting_dict(self):
        dict_to_check = {'wat_2.s.area': 0.0}
        self.check_var_setting_dict(self.mdl, dict_to_check)

    def test_dynamic_prop_values(self):
        """Test that given fault times result in the expected water/value loss"""
        faulttimes = [10, 20, 30]
        for faulttime in faulttimes:
            res, hist = prop.one_fault(self.water_mdl, "move_water", "mech_break",
                                       time=faulttime)
            expected_wcost = self.expected_water_cost(faulttime)
            self.assertAlmostEqual(expected_wcost, res.endclass.cost)

    def test_dynamic_prop_values_2(self):
        """Test that the delayed fault behavior occurs at the time specified"""
        delays = [0, 1, 5, 10]
        for delay in delays:
            mdl = Pump(p={'cost': ('water',), 'delay': delay})
            res, hist = prop.one_fault(mdl, 'export_water', 'block',
                                       time=25, track="all")
            fault_at_time = hist.faulty.fxns.move_water.m.faults.mech_break[25+delay]
            self.assertEqual(fault_at_time, 1)
            fault_bef_time = hist.faulty.fxns.move_water.m.faults.mech_break[25+delay-1]
            self.assertEqual(fault_bef_time, 0)

    def test_app_prop_values(self):
        """Test that the delayed fault behavior occurs at the time specified (with approach)"""
        fd = FaultDomain(self.mdl)
        fd.add_fault('move_water', 'mech_break')
        fs = FaultSample(fd)
        fs.add_fault_phases("on", args=(5,))

        res, hist = prop.fault_sample(self.water_mdl, fs, showprogress=False)
        for scen in fs.scenarios():
            exp_wcost = self.expected_water_cost(scen.time)
            self.assertAlmostEqual(exp_wcost, res.get(scen.name).endclass.cost)

    def expected_water_cost(self, faulttime):
        return (50 - faulttime) * 0.3 * 750

    def test_model_copy_same(self):
        inj_times = [10, 20, 30, 40]
        self.check_model_copy_same(self.mdl, Pump(), inj_times, 30, max_time=55)

    def test_model_copy_different(self):
        inj_times = [10, 20, 30, 40]
        self.check_model_copy_different(self.mdl, inj_times, max_time=55)

    def test_model_reset(self):
        inj_times = [10, 20, 30, 40]
        self.check_model_reset(self.mdl, Pump(), inj_times, max_time=55)

    def test_approach_cost_calc(self):
        """Test that the (linear) resilience loss function is perfectly approximated
        using the given sampling methods"""
        mdl = Pump(p={'cost': ('ee', 'repair', 'water'), 'delay': 0})
        fs_full = FaultSample(self.fd)
        fs_full.add_fault_phases(method='all')
        full_util = exp_cost_quant(fs_full, mdl)

        fs_multipt = FaultSample(self.fd)
        fs_multipt.add_fault_phases(args=(3,))
        multipt_util = exp_cost_quant(fs_multipt, mdl)
        self.assertAlmostEqual(full_util, multipt_util, places=2)

        fs_center = FaultSample(self.fd)
        fs_center.add_fault_phases(args=(1,))
        center_util = exp_cost_quant(fs_center, mdl)
        self.assertAlmostEqual(full_util, center_util, places=2)
        from scipy import integrate
        nodes, weights = integrate._quadrature._cached_roots_legendre(3)
        fs_quad = FaultSample(self.fd)
        fs_quad.add_fault_phases(method='quad', args=(nodes, weights))
        quad_util = exp_cost_quant(fs_quad, mdl)
        self.assertAlmostEqual(full_util, quad_util, places=2)

    def test_approach_parallelism(self):
        """Test whether the pump simulates the same when simulated using parallel or
        staged options"""
        self.check_fs_parallel(self.default_mdl, self.fs)
        fs = FaultSample(self.fd)
        fs.add_fault_phases(args=(4,))
        self.check_fs_parallel(self.default_mdl, fs)

    def test_pickleability(self):
        unpickleable = check_pickleability(Pump(), verbose=False)
        self.assertTrue(unpickleable == [])

    def test_one_run_pickle(self):
        if os.path.exists("single_fault.pkl"):
            os.remove("single_fault.pkl")

        res, hist = prop.one_fault(self.mdl, 'export_water', 'block', time=20,
                                   staged=False, run_stochastic=True, sp={'seed': 10})

        hist.save("single_fault.pkl")
        hist_saved = load("single_fault.pkl", renest_dict=False)
        self.assertCountEqual([*hist.keys()], [*hist_saved.keys()])
        # test to see that all values of the arrays in the hist are the same
        for hist_key in hist:
            np.testing.assert_array_equal(hist[hist_key], hist_saved[hist_key])

        hist.faulty.time[0] = 100
        self.assertNotEqual(hist.faulty.time[0], hist_saved.faulty.time[0])

        os.remove("single_fault.pkl")

    def test_one_run_csv(self):
        if os.path.exists("single_fault.csv"):
            os.remove("single_fault.csv")
        res, hist = prop.one_fault(self.mdl, 'export_water', 'block', time=20,
                                   staged=False, run_stochastic=True, sp={'seed': 10})
        hist.save("single_fault.csv")
        hist_saved = load("single_fault.csv", renest_dict=False, Rclass=History)
        self.assertCountEqual([*hist.keys()], [*hist_saved.keys()])
        # test to see that all values of the arrays in the hist are the same
        for hist_key in hist:
            np.testing.assert_array_equal(hist[hist_key], hist_saved[hist_key])
        os.remove("single_fault.csv")

    def test_one_run_json(self):
        if os.path.exists("single_fault.json"):
            os.remove("single_fault.json")

        res, hist = prop.one_fault(self.mdl, 'export_water', 'block', time=20,
                                   staged=False, run_stochastic=True, sp={'seed': 10})
        hist.save("single_fault.json")
        hist_saved = load("single_fault.json", Rclass=History)
        
        self.assertCountEqual([*hist.keys()], [*hist_saved.keys()])
        # test to see that all values of the arrays in the hist are the same
        for hist_key in hist:
            np.testing.assert_array_equal(hist[hist_key], hist_saved[hist_key])
        os.remove("single_fault.json")

    def test_nominal_save(self):
        for ext in [".pkl", ".csv", ".json"]:
            fnames = "pump_res" + ext, "pump_hist" + ext
            self.check_onerun_save(self.mdl, "nominal", *fnames)

    def test_onefault_save(self):
        faultscen = ('export_water', 'block', 25)
        for ext in [".pkl", ".csv", ".json"]:
            fnames = "pump_res" + ext, "pump_hist" + ext
            self.check_onerun_save(self.mdl, 'one_fault', *fnames, faultscen=faultscen)

    def test_save_load_multfault(self):
        faultscen = {10: {"export_water": ['block']}, 20: {"move_water": ["short"]}}
        for ext in [".pkl", ".csv", ".json"]:
            fnames = "pump_res" + ext, "pump_hist" + ext
            self.check_onerun_save(self.mdl, 'sequence', *fnames, faultscen=faultscen)

    def test_single_faults_save(self):
        self.check_sf_save(self.mdl, "pump_res.pkl", "pump_hist.pkl")
        self.check_sf_save(self.mdl, "pump_res.csv", "pump_hist.csv",)
        self.check_sf_save(self.mdl, "pump_res.json", "pump_hist.json")

    def test_single_faults_isave(self):
        self.check_sf_isave(self.mdl, *self.filenames, "pkl")
        self.check_sf_isave(self.mdl, *self.filenames, "csv")
        self.check_sf_isave(self.mdl, *self.filenames, "json")

    def test_param_sample_save(self):
        self.check_ps_save(self.mdl, self.ps, "pump_res.pkl", "pump_hist.pkl")
        self.check_ps_save(self.mdl, self.ps, "pump_res.csv", "pump_hist.csv")
        self.check_ps_save(self.mdl, self.ps,"pump_res.json", "pump_hist.json")

    def test_param_sample_isave(self):
        self.check_ps_isave(self.mdl, self.ps, *self.filenames, "pkl")
        self.check_ps_isave(self.mdl, self.ps, *self.filenames, "csv")
        self.check_ps_isave(self.mdl, self.ps, *self.filenames, "json")

    def test_nested_sample_save(self):
        self.check_ns_save(self.mdl, self.ps, self.faultdomains, self.faultsamples,
                           "pump_res.pkl", "pump_hist.pkl")
        self.check_ns_save(self.mdl, self.ps, self.faultdomains, self.faultsamples,
                           "pump_res.csv", "pump_hist.csv")
        self.check_ns_save(self.mdl, self.ps, self.faultdomains, self.faultsamples,
                           "pump_res.json", "pump_hist.json")

    def test_nested_sample_isave(self):
        self.check_ns_isave(self.mdl, self.ps, self.faultdomains, self.faultsamples,
                            *self.filenames, "pkl")
        self.check_ns_isave(self.mdl, self.ps, self.faultdomains, self.faultsamples,
                            *self.filenames, "csv")
        self.check_ns_isave(self.mdl, self.ps, self.faultdomains, self.faultsamples,
                            *self.filenames, "json")

    def test_fault_sample_save(self):
        self.check_fs_save(self.mdl, self.fs, "pump_res.pkl", "pump_hist.pkl")
        self.check_fs_save(self.mdl, self.fs, "pump_res.csv", "pump_hist.csv")
        self.check_fs_save(self.mdl, self.fs, "pump_res.json", "pump_hist.json")

    def test_fault_sample_isave(self):
        self.check_fs_isave(self.mdl, self.fs, *self.filenames, "pkl")
        self.check_fs_isave(self.mdl, self.fs, *self.filenames, "csv")
        self.check_fs_isave(self.mdl, self.fs, *self.filenames, "json")

    def test_fmea_options(self):
        fd = FaultDomain(self.mdl)
        fd.add_fault('move_water', 'mech_break')
        fs = FaultSample(fd)
        fs.add_fault_phases("on", args=(5,))

        ec, mdlhists = prop.fault_sample(self.water_mdl, fs, showprogress=False)

        fs2 = FaultSample(fd)
        fs2.add_fault_phases()
        ec2, hist2 = prop.fault_sample(self.mdl, fs2, showprogress=False)


def exp_cost_quant(fs, mdl):
    """ Calculate expected cost of faults over a faultsample for the model."""

    result, mdlhists = prop.fault_sample(mdl, fs, showprogress=False)
    fmea = an.tabulate.FMEA(result, fs)
    util = fmea.as_table()['expected cost'].sum()
    return util

if __name__ == '__main__':
    unittest.main()
    
    #suite = unittest.TestSuite()
    #suite.addTest(PumpTests("test_approach_cost_calc"))
    #suite.addTest(PumpTests("test_value_setting_dict"))
    #suite.addTest(PumpTests("test_one_run_csv"))
    #runner = unittest.TextTestRunner()
    #runner.run(suite)

    
    
