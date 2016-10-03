from epynet import Network
from nose.tools import assert_equal

class TestEpynet(object):
    @classmethod
    def setup_class(self):
        self.network = Network('tests/testnetwork.inp')
        self.network.solve()

    def test1_network(self):
        # test node count
        assert_equal(len(self.network.nodes),11)
        # test link count
        assert_equal(len(self.network.links),12)
        # test reservoir count
        assert_equal(len(self.network.reservoirs),1)
        # test valve count
        assert_equal(len(self.network.valves),1)
        # test pump count
        assert_equal(len(self.network.pumps),1)
        # test tank count
        assert_equal(len(self.network.tanks),1)

    def test2_link(self):
        # test the properties of a single link
        link = self.network.links['11']
        # pipe index and uid
        assert_equal(link.index,9)
        assert_equal(link.uid,'11')
        # from/to node
        assert_equal(link.from_node.uid,'4')
        assert_equal(link.to_node.uid,'9')

    def test3_pipe(self):
        # test the properties of a single pipe
        pipe = self.network.links['11']
        # check type
        assert_equal(pipe.link_type,'pipe')

        assert_equal(pipe.length,100)
        assert_equal(pipe.diameter,150)
        assert_equal(pipe.roughness,0.1)
        assert_equal(round(pipe.minorloss,2),0.1)
        # flow
        assert_equal(round(pipe.flow,2),87.92)
        # direction
        assert_equal(round(pipe.velocity,2),1.38)
        # status
        assert_equal(pipe.status,1)
        # headloss
        assert_equal(round(pipe.headloss,2),1.29)
        # upstream/downstream node
        assert_equal(pipe.upstream_node.uid,'4')
        assert_equal(pipe.downstream_node.uid,'9')

    def test4_pump(self):
        pump = self.network.pumps['2']
        # check type
        assert_equal(pump.link_type,'pump')

        assert_equal(pump.speed,1.0)
        assert_equal(round(pump.flow,2),109.67)
        # change speed
        pump.set_speed(1.5)
        assert_equal(pump.speed,1.5)
        # resolve network
        self.network.solve()
        assert_equal(round(pump.flow,2),164.5)
        # revert speed
        pump.set_speed(1.0)
        self.network.solve()
        
    def test5_valve(self):
        valve = self.network.valves['9']
        # check type
        assert_equal(valve.link_type,'valve')
        # check valve type
        assert_equal(valve.valve_type,'PRV')
        # valve settings
        assert_equal(valve.setting,5)
        assert_equal(round(valve.downstream_node.pressure),5)
        # change setting
        valve.set_setting(10)
        assert_equal(valve.setting,10)
        self.network.solve()
        assert_equal(round(valve.downstream_node.pressure),10)

    def test6_node(self):
        node = self.network.nodes['4']
        # uid
        assert_equal(node.uid,'4')
        # coordinates
        assert_equal(node.coordinates,(2103.02,5747.69))
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

    def test7_junction(self):
        junction = self.network.junctions['4']

        assert_equal(round(junction.basedemand,2),1)
        assert_equal(round(junction.demand,2),1)

    def test8_tank(self):
        tank = self.network.tanks['11']
        assert_equal(tank.diameter,50)
        assert_equal(round(tank.initvolume,2),19634.95)
        assert_equal(tank.minvolume,0)
        assert_equal(tank.minlevel,0)
        assert_equal(tank.maxlevel,20)
        assert_equal(round(tank.volume,2),19634.95)
        assert_equal(round(tank.maxvolume),2*round(tank.volume))

    def test8_time(self):
        junction = self.network.junctions['4']
        self.network.solve(3600)
        assert_equal(round(junction.demand,2),2)
        self.network.solve(7200)
        assert_equal(round(junction.demand,2),3)










