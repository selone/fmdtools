# -*- coding: utf-8 -*-
"""
Created on Mon Dec 20 10:32:00 2021

@author: dhulse
"""
import unittest
from examples.eps.eps import EPS
from fmdtools.sim import propagate as prop
from fmdtools.sim.sample import FaultDomain, FaultSample
from fmdtools.define.common import check_pickleability
import numpy as np
import math
from tests.common import CommonTests


class epsTests(unittest.TestCase, CommonTests):
    def setUp(self):
        self.mdl = EPS()
        self.fd = FaultDomain(self.mdl)
        self.fd.add_all()

    def test_backward_fault_prop_1(self):
        """Tests that defined fault cases that require reverse propagation propagate
        backwards through the graph as expected - distributor short leads to empty battery
        """
        res, hist = prop.one_fault(self.mdl, "distribute_ee", "short",
                                   desired_result="endfaults")
        self.assertEqual(res["endfaults"]["store_ee"], ["no_storage"])

    def test_backward_fault_prop_2(self):
        """Tests that defined fault cases that require reverse propagation propagate
        backwards through the graph as expected - motor short leads to distributor short
        """
        res, hist = prop.one_fault(self.mdl, "ee_to_me", "short",
                                   desired_result="endfaults")
        self.assertEqual(res["endfaults"]["store_ee"], ["no_storage"])
        self.assertEqual(res["endfaults"]["distribute_ee"], ["short"])

    def test_all_faults(self):
        """Some basic tests for propagating lists of faults in the model--
        that histories have length 1, endresults have >0 costs, and total costs are higher
        than repairs"""
        mdl = self.mdl
        res, hist = prop.single_faults(mdl, showprogress=False)
        actual_num_faults = np.sum([len(f.m.faultmodes) for f in mdl.fxns.values()])
        self.assertEqual(len(res.nest(1)), actual_num_faults + 1)
        hist_len_is_1 = all([len(v) == 1 for v in hist.values()])
        self.assertTrue(hist_len_is_1)  # all histories have length 1
        all_have_costs = all(v > 0 for k, v in res.get_values('.cost').items()
                             if 'nominal' not in k)
        self.assertTrue(all_have_costs)  # all endresults have positive costs
        repcosts = np.sum([np.sum([m["cost"] for m in f.m.faultmodes.values()])
                           for f in mdl.fxns.values()])
        # fault costs higher than if it was just repairs
        total_simcosts = sum([v for v in res.get_values('.cost').values()])
        self.assertGreater(total_simcosts, repcosts)

    def test_fault_app(self):
        """Tests that the expected number of scenarios are generated for a given
        approach"""
        tot_faults = [len(f.m.faultmodes) for f in self.mdl.fxns.values()]
        actual_num_faults = int(np.sum(tot_faults))
        for n_joint in [2, 3, actual_num_faults]:
            fs = FaultSample(self.fd)
            fs.add_fault_phases(n_joint=n_joint)
            # tests the length
            self.assertEqual(len(fs.scenarios()), math.comb(actual_num_faults, n_joint))
            ec, hists = prop.fault_sample(self.mdl, fs, showprogress=False)

    def test_pickleability(self):
        unpickleable = check_pickleability(self.mdl, verbose=False)
        self.assertTrue(unpickleable == [])

    def test_nominal_saving(self):
        for extension in [".pkl", ".csv", ".json"]:
            resname = "eps_hist" + extension
            histname = "eps_res" + extension
            self.check_onerun_save(self.mdl, 'nominal', resname, histname)

    def test_save_load_onefault(self):
        faultscen = ("store_ee", "no_storage", 0)
        for extension in [".pkl", ".csv", ".json"]:
            resname = "eps_hist" + extension
            histname = "eps_res" + extension
            self.check_onerun_save(self.mdl, 'one_fault', resname, histname,
                                   faultscen=faultscen)

    def test_multfault_saving(self):
        faultscen = {0: {"store_ee": ["no_storage"], "distribute_ee": "short"}}
        for extension in [".pkl", ".csv", ".json"]:
            resname = "eps_hist" + extension
            histname = "eps_res" + extension
            self.check_onerun_save(self.mdl, "sequence", resname, histname,
                                   faultscen=faultscen)

    def test_save_load_singlefaults(self):
        self.check_sf_save(self.mdl, "eps_res.pkl", "eps_hist.pkl")
        self.check_sf_save(self.mdl, "eps_res.csv", "eps_hist.csv")
        self.check_sf_save(self.mdl, "eps_res.json", "eps_hist.json")


if __name__ == "__main__":
    unittest.main()

    mdl = EPS()


    # endresults, resgraph, mdlhist = propagate.one_fault(mdl, 'Distribute_EE', 'short')

    # mdl = EPS()
    # endresults, resgraph, mdlhist = propagate.one_fault(mdl, 'EE_to_ME', 'short')

    # mdl_nom = EPS()
    # endresults_nom, resgraph_nom, mdlhist_nom = propagate.nominal(mdl_nom)

    # endclasses, reshists = propagate.single_faults(mdl)
