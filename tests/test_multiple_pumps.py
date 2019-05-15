from epynet import Network
from nose.tools import assert_equal, assert_almost_equal
import pandas as pd


class TestMultiplePumps(object):
    @classmethod
    def setup_class(self):
        self.network = Network()


    def test01_multiple_pumps(self):

        network = self.network

        network.add_reservoir("R1", 0, 0, 0)
        network.add_junction("J1", 1, 0)
        network.add_junction("J2", 2, 0)
        network.add_junction("J3", 3, 0)
        network.add_junction("J4", 4, 0)
        network.add_reservoir("R2", 5, 0, 0)

        network.add_pipe("P1", "R1", "J1", 200, 100)
        network.add_pipe("P2", "J2", "J4", 200, 100)
        network.add_pipe("P3", "J3", "J4", 200, 100)
        network.add_pipe("P4", "J4", "R2", 200, 100)

        P1 = network.add_pump("PU1", "J1", "J2", 1)
        P2 = network.add_pump("PU2", "J1", "J3", 1)

        C1 = network.add_curve("1", [[100, 30], [200, 20], [300, 10]])
        C2 = network.add_curve("2", [[100, 40], [200, 25], [300, 10]])

        P1.curve = C1
        P2.curve = C2

        network.solve()

        assert_almost_equal(P1.flow, 225.88, 2)
        assert_almost_equal(P2.flow, 248.14, 2)

        C3 = network.add_curve("3", [[100, 30]])
        C4 = network.add_curve("4", [[100, 50]])

        P1.curve = C3
        P2.curve = C4

        network.solve()

        assert_almost_equal(P1.flow, 173.09, 2)
        assert_almost_equal(P2.flow, 184.10, 2)
