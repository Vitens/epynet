from epynet import Network, epanet2
from nose.tools import assert_equal, assert_almost_equal
import pandas as pd

class TestGeneratedNetwork(object):

    @classmethod
    def setup_class(self):
        self.network = Network()

    @classmethod
    def teadown(self):
        self.network.ep.ENclose()

    def test00_build_network(self):
        network = self.network

        network.ep.ENsettimeparam(epanet2.EN_DURATION, 10*3600)
        # add nodes
        reservoir = network.add_reservoir('in',0,30)
        reservoir.elevation = 10

        pattern_values = [1,2,3,4,5,4,3,2,1,1]

        pattern = network.add_pattern('1',pattern_values)

        junctions = {'2':(10,30,0), 
                     '3':(20,30,0), 
                     '4':(30,30,1), 
                     '5':(30,20,1),
                     '6':(30,10,1), 
                     '7':(40,10,1), 
                     '8':(40,20,1), 
                     '9':(40,30,1),
                     '10':(50,30,1)}

        links = {'1':('in','2'),
                 '3':('3','4'),
                 '4':('4','5'),
                 '5':('5','6'),
                 '6':('6','7'),
                 '7':('7','8'),
                 '8':('8','9'),
                 '10':('5','8'),
                 '11':('4','9'),
                 '12':('9','11')}

        for uid, coord in junctions.items():
            node = network.add_junction(uid, coord[0], coord[1], elevation=0, basedemand=coord[2])
            node.pattern = pattern

        tank = network.add_tank('11',40,40, diameter=50, maxlevel=20, minlevel=0, tanklevel=10)

        for uid, coord in links.items():
            link = network.add_pipe(uid, coord[0], coord[1], diameter=100, length=100, roughness=0.1)

        valve = network.add_valve('9','prv','9','10', diameter=100, setting=5)

        pump = network.add_pump('2','2','3', speed=1)

        curve = network.add_curve('1',[(100,50)])
        pump.curve = curve

        network.nodes['4'].elevation = 5
        network.links['11'].diameter = 150
        network.links['11'].minorloss = 0.1

        network.solve()

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
        #coordinates = node.coordinates
        # dont test these for created networks
        #assert_almost_equal(coordinates[0],2103.02,2)
        #assert_almost_equal(coordinates[1],5747.69,2)
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
        self.network.solve()
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
        print(type(self.network.pipes['1'].velocity))
        assert(isinstance(self.network.pipes['1'].velocity, float))
        assert(isinstance(self.network.pipes.velocity, pd.Series))

