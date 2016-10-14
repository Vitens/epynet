from epynet import Network
from nose.tools import assert_equal, assert_almost_equal
import pandas as pd

class TestEpynet(object):
    @classmethod
    def setup_class(self):
        self.network = Network('tests/testnetwork.inp')
        self.network.solve()

    def test01_network(self):
        # test0 node count
        assert_equal(len(self.network.nodes),11)
        # test0 link count
        assert_equal(len(self.network.links),12)
        # test0 reservoir count
        assert_equal(len(self.network.reservoirs),1)
        # test0 valve count
        assert_equal(len(self.network.valves),1)
        # test0 pump count
        assert_equal(len(self.network.pumps),1)
        # test0 tank count
        assert_equal(len(self.network.tanks),1)

    def test02_link(self):
        # test0 the properties of a single link
        link = self.network.links['11']
        # pipe index and uid
        assert_equal(link.index,9)
        assert_equal(link.uid,'11')
        # from/to node
        assert_equal(link.from_node.uid,'4')
        assert_equal(link.to_node.uid,'9')

    def test03_pipe(self):
        # test0 the properties of a single pipe
        pipe = self.network.links['11']
        # check type
        assert_equal(pipe.link_type,'pipe')

        assert_almost_equal(pipe.length,100,2)
        assert_almost_equal(pipe.diameter,150,2)
        assert_almost_equal(pipe.roughness,0.1,2)
        assert_almost_equal(pipe.minorloss,0.1,2)
        # flow
        assert_almost_equal(pipe.flow,87.92,2)
        # direction
        assert_almost_equal(pipe.velocity,1.38,2)
        # status
        assert_equal(pipe.status,1)
        # headloss
        assert_almost_equal(pipe.headloss,1.29,2)
        # upstream/downstream node
        assert_equal(pipe.upstream_node.uid,'4')
        assert_equal(pipe.downstream_node.uid,'9')

    def test04_pump(self):
        pump = self.network.pumps['2']
        # check type
        assert_equal(pump.link_type,'pump')

        assert_equal(pump.speed,1.0)
        assert_almost_equal(pump.flow,109.67,2)
        # change speed
        pump.speed = 1.5
        assert_equal(pump.speed,1.5)
        # resolve network
        self.network.solve()
        assert_almost_equal(pump.flow,164.5,2)
        # revert speed
        pump.speed = 1.0
        self.network.solve()
        
    def test05_valve(self):
        valve = self.network.valves['9']
        # check type
        assert_equal(valve.link_type,'valve')
        # check valve type
        assert_equal(valve.valve_type,'PRV')
        # valve settings
        assert_equal(valve.setting,5)
        assert_almost_equal(valve.downstream_node.pressure,5,2)
        # change setting
        valve.setting = 10
        assert_equal(valve.setting,10)
        self.network.solve()
        assert_almost_equal(valve.downstream_node.pressure,10,2)

    def test06_node(self):
        node = self.network.nodes['4']
        # uid
        assert_equal(node.uid,'4')
        # coordinates
        coordinates = node.coordinates
        assert_almost_equal(coordinates[0],2103.02,2)
        assert_almost_equal(coordinates[1],5747.69,2)
        # links
        assert_equal(len(node.links),3)
        # up and downstream links
        assert_equal(len(node.downstream_links),2)
        assert_equal(len(node.upstream_links),1)
        # inflow
        assert_equal(round(node.inflow,2),109.67)
        # outflow
        assert_equal(round(node.outflow,2),round(node.inflow,2)-node.demand)
        # elevation
        assert_equal(node.elevation,5)
        # head
        assert_equal(round(node.head,2),25.13)

    def test07_junction(self):
        junction = self.network.junctions['4']

        assert_equal(round(junction.basedemand,2),1)
        assert_equal(round(junction.demand,2),1)

    def test08_tank(self):
        tank = self.network.tanks['11']
        assert_equal(tank.diameter,50)
        assert_equal(round(tank.initvolume,2),19634.95)
        assert_equal(tank.minvolume,0)
        assert_equal(tank.minlevel,0)
        assert_equal(tank.maxlevel,20)
        assert_equal(round(tank.volume,2),19634.95)
        assert_equal(round(tank.maxvolume),2*round(tank.volume))

    def test09_time(self):
        junction = self.network.junctions['4']
        self.network.solve(3600)
        assert_equal(round(junction.demand,2),2)
        self.network.solve(7200)
        assert_equal(round(junction.demand,2),3)

    def test10_collections(self):
        # collection attributes as pandas Series
        assert_almost_equal(self.network.pipes.flow.mean(),46.77,2)
        assert_almost_equal(self.network.pipes.diameter.max(),150,2)
        assert_almost_equal(self.network.pipes.velocity.min(),0.105,2)

        assert_equal(self.network.valves.setting.mean(),10)

        assert_almost_equal(self.network.junctions.demand.mean(),2.33,2)

        # filtering and slicing collections
        assert_equal(len(self.network.pipes[self.network.pipes.velocity > 3]),3)
        assert_equal(len(self.network.nodes[self.network.nodes.pressure < 20]),5)

        #increase the size of all pipes
        self.network.pipes.diameter += 500
        assert_almost_equal(self.network.pipes.diameter.mean(),605,2)

        self.network.pipes.diameter -= 500

        # resize pipes, and recalculate velocity
        self.network.pipes[self.network.pipes.velocity > 3].diameter += 100
        self.network.solve()

        assert_equal(len(self.network.pipes[self.network.pipes.velocity > 3]),0)

    def test11_timeseries(self):
        # run network
        self.network.run()
        # check return types
        # should return Series
        assert(isinstance(self.network.pipes['1'].velocity, pd.Series))
        # should return Dataframe
        assert(isinstance(self.network.pipes.velocity, pd.DataFrame))

        # timeseries operations
        # pipe 1 max velocity
        assert_almost_equal(self.network.pipes['1'].velocity.mean(),1.66,2)
        # all day mean velocity
        assert_almost_equal(self.network.pipes.velocity.mean().mean(),1.14,2)

        # test revert to steady state calculation
        self.network.solve()
        assert(isinstance(self.network.pipes['1'].velocity, float))
        assert(isinstance(self.network.pipes.velocity, pd.Series))

