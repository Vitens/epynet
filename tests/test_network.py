import pytest
from epynet import Network
import pandas as pd

class TestNetwork:
    @classmethod
    def setup_class(cls):
        cls.network = Network(inputfile="tests/testnetwork.inp")
        cls.network.solve()

    @classmethod
    def teardown_method(cls):
        cls.network.ep.ENcloseH()

    def test01_network(self):
        # test node count
        assert len(self.network.nodes) == 11
        # test link count
        assert len(self.network.links) == 12
        # test reservoir count
        assert len(self.network.reservoirs) == 1
        # test valve count
        assert len(self.network.valves) == 1
        # test pump count
        assert len(self.network.pumps) == 1
        # test tank count
        assert len(self.network.tanks) == 1

    def test02_link(self):
        # test the properties of a single link
        link = self.network.links["11"]
        # pipe index and uid
        assert link.index == 9
        assert link.uid == "11"
        # from/to node
        assert link.from_node.uid == "4"
        assert link.to_node.uid == "9"

    def test03_pipe(self):
        # test the properties of a single pipe
        pipe = self.network.links["11"]
        # check type
        assert pipe.link_type == "pipe"

        assert pytest.approx(pipe.length, 2) == 100
        assert pytest.approx(pipe.diameter, 2) == 150
        assert pytest.approx(pipe.roughness, 2) == 0.1
        assert pytest.approx(pipe.minorloss, 2) == 0.1
        # flow
        assert pytest.approx(pipe.flow, 2) == 87.92
        # direction
        assert pytest.approx(pipe.velocity, 2) == 1.38
        # status
        assert pipe.status == 1
        # headloss
        assert pytest.approx(pipe.headloss, 2) == 1.29
        # upstream/downstream node
        assert pipe.upstream_node.uid == "4"
        assert pipe.downstream_node.uid == "9"

    def test04_pump(self):
        pump = self.network.pumps["2"]
        # check type
        assert pump.link_type == "pump"

        assert pump.speed == 1.0
        assert pytest.approx(pump.flow, 2) == 109.67
        # change speed
        pump.speed = 1.5
        assert pump.speed == 1.5
        # resolve network
        self.network.solve()
        assert pytest.approx(pump.flow, 2) == 164.5
        # revert speed
        pump.speed = 1.0
        self.network.solve()

    def test05_valve(self):
        valve = self.network.valves["9"]
        # check type
        assert valve.link_type == "valve"
        # check valve type
        assert valve.valve_type == "PRV"
        # valve settings
        assert valve.setting == 5
        assert pytest.approx(valve.downstream_node.pressure, 2) == 5
        # change setting
        valve.setting = 10
        assert valve.setting == 10
        self.network.solve()
        assert pytest.approx(valve.downstream_node.pressure, 2) == 10

    def test06_node(self):
        node = self.network.nodes["4"]
        # uid
        assert node.uid == "4"
        # coordinates
        coordinates = node.coordinates
        assert pytest.approx(coordinates[0], 2) == 2103.02
        assert pytest.approx(coordinates[1], 2) == 5747.69
        # links
        assert len(node.links) == 3
        # up and downstream links
        assert len(node.downstream_links) == 2
        assert len(node.upstream_links) == 1
        # inflow
        assert round(node.inflow, 2) == 109.67
        # outflow
        assert round(node.outflow, 2) == round(node.inflow, 2) - node.demand
        # elevation
        assert node.elevation == 5
        # head
        assert pytest.approx(round(node.head, 2), 2) == 25.13

    def test07_junction(self):
        junction = self.network.junctions["4"]

        assert pytest.approx(round(junction.basedemand, 2), 2) == 1
        assert pytest.approx(round(junction.demand, 2), 2) == 1

    def test08_tank(self):
        tank = self.network.tanks["11"]
        assert pytest.approx(round(tank.diameter, 2), 2) == 50
        assert pytest.approx(round(tank.initvolume, 2), 2) == 19634.95
        assert tank.minvolume == 0
        assert tank.minlevel == 0
        assert tank.maxlevel == 20
        assert pytest.approx(round(tank.volume, 2), 2) == 19634.95
        assert pytest.approx(round(tank.maxvolume), 2) == 2 * round(tank.volume)

    def test09_time(self):
        junction = self.network.junctions["4"]
        self.network.solve(3600)
        assert pytest.approx(round(junction.demand, 2), 2) == 2
        self.network.solve(7200)
        assert pytest.approx(round(junction.demand, 2), 2) == 3

    def test10_collections(self):
        # collection attributes as pandas Series
        assert pytest.approx(self.network.pipes.flow.mean(), 2) == 46.78
        assert pytest.approx(self.network.pipes.diameter.max(), 2) == 150
        assert pytest.approx(self.network.pipes.velocity.min(), 2) == 0.105

        assert self.network.valves.setting.mean() == 10

        assert pytest.approx(self.network.junctions.demand.mean(), 2) == 2.33

        # filtering and slicing collections
        assert len(self.network.pipes[self.network.pipes.velocity > 3]) == 3
        assert len(self.network.nodes[self.network.nodes.pressure < 20]) == 5

        # increase the size of all pipes
        self.network.pipes.diameter += 500
        assert pytest.approx(self.network.pipes.diameter.mean(), 2) == 605

        self.network.pipes.diameter -= 500
        self.network.solve()

        # resize pipes, and recalculate velocity
        self.network.pipes[self.network.pipes.velocity > 3].diameter += 100
        self.network.solve()

        assert len(self.network.pipes[self.network.pipes.velocity > 3]) == 0

    def test11_timeseries(self):
        # run network
        self.network.run()
        # check return types
        # should return Series
        assert isinstance(self.network.pipes["1"].velocity, pd.Series)
        # should return DataFrame
        assert isinstance(self.network.pipes.velocity, pd.DataFrame)

        # timeseries operations
        # pipe 1 max velocity
        assert pytest.approx(self.network.pipes["1"].velocity.mean(), 2) == 1.66
        # all day mean velocity
        assert pytest.approx(self.network.pipes.velocity.mean().mean(), 2) == 1.14

        # test revert to steady state calculation
        self.network.solve()
        assert isinstance(self.network.pipes["1"].velocity, float)
        assert isinstance(self.network.pipes.velocity, pd.Series)

    def test12_comments(self):
        # test reading comments
        assert self.network.links["1"].comment == "testcommentpipe"
        assert self.network.reservoirs["in"].comment == "testcommentreservoir"
        assert self.network.tanks["11"].comment == "testcommenttank"
        assert self.network.junctions["2"].comment == "testcommentjunction"

        # test writing comments
        self.network.links["1"].comment = "testwrite"
        assert self.network.links["1"].comment == "testwrite"
