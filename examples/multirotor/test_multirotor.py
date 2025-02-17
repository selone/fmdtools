# -*- coding: utf-8 -*-
"""
Created on Wed Dec 14 13:51:18 2022

@author: dhulse
"""
import unittest
from examples.multirotor.opt_drone_rural import opt_prob, x_to_rcost, x_to_ocost
from examples.multirotor.drone_mdl_rural import Drone
import multiprocessing as mp

class DroneTests(unittest.TestCase):
    def test_interface_values(self):
        
        testvalues = [[0,0, 50, 0,0], [0,2, 100, 1,1],[2,2, 150, 1,1]]
        # NOTE: because there is a fault in the nominal sim that triggers the resilience policy
        # the value [2,2, 50, 0,0] will give inconsistent results, since the operational model
        # doesn't have a consistent resilience policy in that case
        for testvalue in testvalues:
        
            rcost_manual = x_to_rcost(testvalue[:2], [testvalue[2]], testvalue[3:], faultmodes='store_ee')
            rcost_int = opt_prob.cr(testvalue)
            self.assertAlmostEqual(rcost_manual/10000, rcost_int/10000, 1)
    def test_sim_types(self):
        # TODO: Investigate discrepancy between values
        testvalue= [0,2, 100, 1,1]
        #rcost_manual = x_to_rcost(testvalue[:2], [testvalue[2]], testvalue[3:], faultmodes='store_ee')
        
        opt_prob.update_sim_options("rcost", staged=False, pool=mp.Pool(4))
        rcost_int = opt_prob.cr(testvalue)
        #self.assertAlmostEqual(rcost_manual/10000, rcost_int/10000, 1)
        
        opt_prob.update_sim_options("rcost", staged=True, pool=mp.Pool(4))
        rcost_int = opt_prob.cr(testvalue)
        #self.assertAlmostEqual(rcost_manual/10000, rcost_int/10000, 1)
        
        opt_prob.update_sim_options("rcost", staged=True, pool=False) 
        rcost_int = opt_prob.cr(testvalue)

        
        #self.assertAlmostEqual(rcost_manual/10000, rcost_int/10000, 1)
        

if __name__ == '__main__':
    
    unittest.main()
    
    #suite = unittest.TestSuite()
    #suite.addTest(DroneTests("test_sim_types"))
    #runner = unittest.TextTestRunner()
    #runner.run(suite)
        
