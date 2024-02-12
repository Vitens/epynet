""" EPYNET Classes """
import numpy as np
from . import epanet2
from .curve import Curve
from .link import Pipe, Valve, Pump
from .node import Junction, Tank, Reservoir
from .objectcollection import ObjectCollection
from .pattern import Pattern


def isList(var):
    if isinstance(var, (list, np.ndarray, np.matrix)):
        return True
    else:
        return False

class Network(object):
    """ self.epANET Network Simulation Class """

    def __init__(self, inputfile=None, units=epanet2.EN_CMH, headloss=epanet2.EN_DW, charset='UTF8'):

        # create multithreaded EPANET instance
        self.ToolkitConstants = ['EN_NODECOUNT', 'EN_TANKCOUNT']
        self.ep = epanet2.EPANET2(charset=charset)

        if inputfile:
            self.inputfile = inputfile
            self.rptfile = self.inputfile[:-3] + "rpt"
            self.binfile = self.inputfile[:-3] + "bin"
            self.ep.ENopen(self.inputfile, self.rptfile, self.binfile)
        else:
            self.inputfile = False

            self.rptfile = ""
            self.binfile = ""

            self.ep.ENinit(self.rptfile.encode(), self.binfile.encode(), units, headloss)

        self.vertices = {}
        # prepare network data
        self.nodes = ObjectCollection()
        self.junctions = ObjectCollection()
        self.reservoirs = ObjectCollection()
        self.tanks = ObjectCollection()

        self.links = ObjectCollection()
        self.pipes = ObjectCollection()
        self.valves = ObjectCollection()
        self.pumps = ObjectCollection()

        self.curves = ObjectCollection()
        self.patterns = ObjectCollection()

        self.solved = False
        self.solved_for_simtime = None

        self.load_network()
        # Link Status
        self.TYPESTATUS = ['CLOSED', 'OPEN']
        # Constants for control: 'LOWLEVEL', 'HILEVEL', 'TIMER', 'TIMEOFDAY'
        self.TYPECONTROL = ['LOWLEVEL', 'HIGHLEVEL', 'TIMER', 'TIMEOFDAY']


    def load_network(self):
        """
        Load network data
        """
        # load nodes
        global link
        for index in range(1, self.ep.ENgetcount(epanet2.EN_NODECOUNT) + 1):
            # get node type
            node_type = self.ep.ENgetnodetype(index)
            uid = self.ep.ENgetnodeid(index)

            if node_type == 0:
                node = Junction(uid, self)
                self.junctions[node.uid] = node
            elif node_type == 1:
                node = Reservoir(uid, self)
                self.reservoirs[node.uid] = node
                self.nodes[node.uid] = node
            else:
                node = Tank(uid, self)
                self.tanks[node.uid] = node

            self.nodes[node.uid] = node

        # load links
        for index in range(1, self.ep.ENgetcount(epanet2.EN_LINKCOUNT) + 1):
            link_type = self.ep.ENgetlinktype(index)
            uid = self.ep.ENgetlinkid(index)
            # pipes
            if link_type <= 1:
                link = Pipe(uid, self)
                self.pipes[link.uid] = link
            elif link_type == 2:
                link = Pump(uid, self)
                self.pumps[link.uid] = link
            elif link_type >= 3:
                link = Valve(uid, self)
                self.valves[link.uid] = link

            self.links[link.uid] = link
            link_nodes = self.ep.ENgetlinknodes(index)
            link.from_node = self.nodes[self.ep.ENgetnodeid(link_nodes[0])]
            link.from_node.links[link.uid] = link
            link.to_node = self.nodes[self.ep.ENgetnodeid(link_nodes[1])]
            link.to_node.links[link.uid] = link

        # load curves				  
        for index in range(1, self.ep.ENgetcount(epanet2.EN_CURVECOUNT) + 1):
            uid = self.ep.ENgetcurveid(index)
            self.curves[uid] = Curve(uid, self)

        # load patterns
        for index in range(1, self.ep.ENgetcount(epanet2.EN_PATCOUNT) + 1):
            uid = self.ep.ENgetpatternid(index)
            self.patterns[uid] = Pattern(uid, self)

    def reset(self):

        self.solved = False
        self.solved_for_simtime = None

        for link in self.links:
            link.reset()
        for node in self.nodes:
            node.reset()

    def delete_node(self, uid):
        index = self.ep.ENgetnodeindex(uid)
        node_type = self.ep.ENgetnodetype(index)

        for link in list(self.nodes[uid].links):
            self.delete_link(link.uid)

        del self.nodes[uid]

        if node_type == epanet2.EN_JUNCTION:
            del self.junctions[uid]
        elif node_type == epanet2.EN_RESERVOIR:
            del self.reservoirs[uid]
        elif node_type == epanet2.EN_TANK:
            del self.tanks[uid]

        self.ep.ENdeletenode(index)

        self.invalidate_nodes()
        self.invalidate_links()

    def delete_link(self, uid):

        index = self.ep.ENgetlinkindex(uid)
        link_type = self.ep.ENgetlinktype(index)

        link = self.links[uid]
        del link.from_node.links[uid]
        del link.to_node.links[uid]

        del self.links[uid]

        if link_type == epanet2.EN_PIPE or link_type == epanet2.EN_CVPIPE:
            del self.pipes[uid]
        elif link_type == epanet2.EN_PUMP:
            del self.pumps[uid]
        else:
            del self.valves[uid]

        self.ep.ENdeletelink(index)

        self.invalidate_nodes()
        self.invalidate_links()

    def add_reservoir(self, uid, x, y, elevation=0):

        self.ep.ENaddnode(uid, epanet2.EN_RESERVOIR)

        index = self.ep.ENgetnodeindex(uid)

        self.ep.ENsetcoord(index, x, y)

        node = Reservoir(uid, self)
        node.elevation = elevation

        self.reservoirs[uid] = node
        self.nodes[uid] = node

        self.invalidate_nodes()

        return node

    def add_junction(self, uid, x, y, basedemand=0, elevation=0):
        self.ep.ENaddnode(uid, epanet2.EN_JUNCTION)
        index = self.ep.ENgetnodeindex(uid)
        self.ep.ENsetcoord(index, x, y)
        node = Junction(uid, self)
        self.junctions[uid] = node
        self.nodes[uid] = node

        # configure node
        node.basedemand = basedemand
        node.elevation = elevation

        self.invalidate_nodes()

        return node

    def add_tank(self, uid, x, y, elevation=0, initlevel=1, minlevel=0, maxlevel=1, diameter=35.6824, minvol=0,
                 volcur=""):
        self.ep.ENaddnode(uid, epanet2.EN_TANK)
        """ adds a tank with a standard volume of 1000 m3
         the default values can be adjusted by setting the following parameters:
                    elevation   : the tank's bottom elevation.
                    initlevel   : the initial water level in the tank.
                    minlevel    : the minimum water level for the tank.
                    maxlevel    : the maximum water level for the tank.
                    diameter    : the tank's diameter (0 if a volume curve is supplied).
                    minvol      : the volume of the tank at its minimum water level.
                    tanklevel   : the name of the tank's volume curve ("" for no curve)
        """
        index = self.ep.ENgetnodeindex(uid)
        self.ep.ENsetcoord(index, x, y)
        self.ep.ENsettankdata(index, elevation, initlevel, minlevel, maxlevel, diameter, minvol, volcur)
        node = Tank(uid, self)

        self.invalidate_nodes()

        return node

    def add_pipe(self, uid, from_node, to_node, diameter=100, length=10, roughness=0.1, check_valve=False):

        from_node = from_node if isinstance(from_node, str) else from_node.uid
        to_node = to_node if isinstance(to_node, str) else to_node.uid

        if check_valve:
            self.ep.ENaddlink(uid, epanet2.EN_CVPIPE, from_node, to_node)
        else:
            self.ep.ENaddlink(uid, epanet2.EN_PIPE, from_node, to_node)

        link = Pipe(uid, self)

        link.diameter = diameter
        link.length = length
        link.roughness = roughness

        link.from_node = self.nodes[from_node]
        link.to_node = self.nodes[to_node]
        link.to_node.links[link.uid] = link
        link.from_node.links[link.uid] = link
        self.pipes[uid] = link
        self.links[uid] = link

        # set link properties
        link.diameter = diameter
        link.length = length

        self.invalidate_links()

        return link

    def add_pump(self, uid, from_node, to_node, speed=0):

        from_node = from_node if isinstance(from_node, str) else from_node.uid
        to_node = to_node if isinstance(to_node, str) else to_node.uid

        self.ep.ENaddlink(uid, epanet2.EN_PUMP, from_node, to_node)
        link = Pump(uid, self)
        link.speed = speed
        link.from_node = self.nodes[from_node]
        link.speed = speed
        link.to_node = self.nodes[to_node]
        link.to_node.links[link.uid] = link
        link.from_node.links[link.uid] = link
        self.pumps[uid] = link
        self.links[uid] = link

        self.invalidate_links()

        return link

    def add_curve(self, uid, values):
        self.ep.ENaddcurve(uid)

        curve = Curve(uid, self)
        curve.values = values
        self.curves[uid] = curve

        return curve

    def add_pattern(self, uid, values):
        self.ep.ENaddpattern(uid)
        pattern = Pattern(uid, self)
        pattern.values = values
        self.patterns[uid] = pattern

        return pattern

    def add_valve_gpv(self, uid, from_node, to_node):
        from_node = from_node if isinstance(from_node, str) else from_node.uid
        to_node = to_node if isinstance(to_node, str) else to_node.uid

        self.ep.ENaddlink(uid, epanet2.EN_GPV, from_node, to_node)
        self.ep.ENsetlinkvalue(self.ep.ENgetlinkindex(uid), 25, 1)
        link = Valve(uid, self)
        self.valves[uid] = link
        self.links[uid] = link

        self.invalidate_links()

        return link

    def add_valve(self, uid, valve_type, from_node, to_node, diameter=100, setting=0):

        from_node = from_node if isinstance(from_node, str) else from_node.uid
        to_node = to_node if isinstance(to_node, str) else to_node.uid

        if valve_type.lower() == "gpv":
            valve_type_code = epanet2.EN_GPV
        elif valve_type.lower() == "fcv":
            valve_type_code = epanet2.EN_FCV
        elif valve_type.lower() == "pbv":
            valve_type_code = epanet2.EN_PBV
        elif valve_type.lower() == "tcv":
            valve_type_code = epanet2.EN_TCV
        elif valve_type.lower() == "prv":
            valve_type_code = epanet2.EN_PRV
        elif valve_type.lower() == "psv":
            valve_type_code = epanet2.EN_PSV
        elif valve_type.lower() == "pcv":
            valve_type_code = epanet2.EN_PCV
        else:
            raise ValueError("Unknown Valve Type")

        self.ep.ENaddlink(uid, valve_type_code, from_node, to_node)
        link = Valve(uid, self)
        link.diameter = diameter
        link.setting = setting
        link.from_node = self.nodes[from_node]
        link.to_node = self.nodes[to_node]
        link.to_node.links[link.uid] = link
        link.from_node.links[link.uid] = link
        self.valves[uid] = link
        self.links[uid] = link

        self.invalidate_links()

        return link

    def invalidate_links(self):
        # set network as unsolved
        self.solved = False
        # reset link index caches
        for link in self.links:
            link._index = None

    def invalidate_nodes(self):
        # set network as unsolved
        self.solved = False
        # reset node index caches
        for node in self.nodes:
            node._index = None

    def solve(self, simtime=0):
        """ Solve Hydraulic Network for Single Timestep"""
        if self.solved and self.solved_for_simtime == simtime:
            return

        self.reset()
        self.ep.ENsettimeparam(4, simtime)
        self.ep.ENopenH()
        self.ep.ENinitH(0)
        self.ep.ENrunH()
        self.ep.ENcloseH()
        self.solved = True
        self.solved_for_simtime = simtime

    def run(self):
        self.reset()
        self.time = []
        # open network
        self.ep.ENopenH()
        self.ep.ENinitH(0)

        self.ep.ENopenQ()
        self.ep.ENinitQ()

        simtime = 0
        timestep = 1
        qstep = 1

        self.solved = True

        while timestep > 0:
            self.ep.ENrunH()
            self.ep.ENrunQ()
            timestep = self.ep.ENnextH()
            self.ep.ENnextQ()
            self.time.append(simtime)
            self.load_attributes(simtime)
            simtime += timestep

        self.ep.ENcloseH()
        self.ep.ENcloseQ()

    def load_attributes(self, simtime):
        for node in self.nodes:
            for property_name in node.properties.keys():
                if property_name not in node.results.keys():
                    node.results[property_name] = []
                # clear cached values
                node._values = {}
                node.results[property_name].append(node.get_property(node.properties[property_name]))
            node.times.append(simtime)

        for link in self.links:
            for property_name in link.properties.keys():
                if property_name not in link.results.keys():
                    link.results[property_name] = []
                # clear cached values
                link._values = {}
                link.results[property_name].append(link.get_property(link.properties[property_name]))
            link.times.append(simtime)

    def save_inputfile(self, name):
        self.ep.ENsaveinpfile(name)

    def get_vertices(self, link_uid):
        if self.vertices == {}:
            self.parse_vertices()
        return self.vertices.get(link_uid, [])

    def parse_vertices(self):
        vertices = False
        if not self.inputfile or len(self.vertices) > 0:
            return

        with open(self.inputfile, 'rb') as handle:
            for line in handle.readlines():
                if b'[VERTICES]' in line:
                    vertices = True
                    continue
                elif b'[' in line:
                    vertices = False

                if b";" in line:
                    continue

                if vertices:
                    components = [c.strip() for c in line.decode(self.ep.charset).split()]
                    if len(components) < 3:
                        continue
                    if components[0] not in self.vertices:
                        self.vertices[components[0]] = []
                    self.vertices[components[0]].append((float(components[1]), float(components[2])))

    def close(self):
        print('closing')
        self.ep.ENdeleteproject()
    def arange(self, begin, end, step=1):
        """ Create float number sequence

        """
        return np.arange(begin, end, step)

    def get_NumNodes(self):
        """" Get number of junctions

        """

        return self.ep.ENgetcount(0)

    def get_NodeIndex(self, *argv):
        values = []
        if len(argv) > 0:
            index = argv[0]
            if isinstance(index, list):
                for i in index:
                    values.append(self.ep.ENgetnodeindex(i))
            else:
                values = self.ep.ENgetnodeindex(index)
        else:
            for i in range(self.get_NumNodes()):
                values.append(i + 1)
        return values

    def get_NodeReservoirIndex(self, *argv):
        """ Retrieves the indices of reservoirs.

        Example 1:

        net.get_NodeReservoirIndex()           # Retrieves the indices of all reservoirs.

        Example 2:

        net.get_NodeReservoirIndex([1,2,3])    # Retrieves the indices of the first 3 reservoirs, if they exist.

        See also getNodeNameID, getNodeIndex, getNodeJunctionIndex,
        getNodeType, getNodeTypeIndex, getNodesInfo.
        """
        tmpNodeTypes = self.get_NodeIndex()
        value = [i for i, x in enumerate(tmpNodeTypes) if x == 1]
        if (len(value) > 0) and (len(argv) > 0):
            index = argv[0]
            try:
                if isinstance(index, list):
                    rIndices = []
                    for i in index:
                        rIndices.append(value[i - 1] + 1)
                    return rIndices
                else:
                    return value[index - 1] + 1
            except:
                raise Exception('Some RESERVOIR indices do not exist.')
        else:
            rIndices = value
            return [i + 1 for i in rIndices]

    def get_NodeDemandIndex(self, *argv):

        value = []
        if len(argv) == 2:
            nodeIndex = argv[0]
            demandName = argv[1]
            if not isList(nodeIndex) and not isList(demandName):
                value = self.ep.ENgetdemandindex(nodeIndex, demandName)
            elif isList(nodeIndex) and isList(demandName):
                value = []
                for i in range(len(nodeIndex)):
                    value.append(self.ep.ENgetdemandindex(nodeIndex[i], demandName[i]))
        elif len(argv) == 1:
            nodeIndex = argv[0]
            demandName = self.get_NodeDemandName()
            if not isList(nodeIndex):
                value = []
                for i in range(len(demandName)):
                    demandNameIn = demandName[i + 1]
                    value.append(self.api.ENgetdemandindex(nodeIndex, demandNameIn[nodeIndex - 1]))
            else:
                value = [[0 for i in range(len(nodeIndex))] for j in range(len(demandName))]
                for i in range(len(demandName)):
                    demandNameIn = demandName[i + 1]
                    for j in range(len(nodeIndex)):
                        value[i][j] = self.api.ENgetdemandindex(nodeIndex[j], demandNameIn[nodeIndex[j] - 1])
        elif len(argv) == 0:
            demandName = self.getNodeJunctionDemandName()
            indices = self.__getNodeJunctionIndices(*argv)
            value = [[0 for _ in range(len(indices))] for _ in range(len(demandName))]
            for i in range(len(demandName)):
                for j in range(len(demandName[i + 1])):
                    demandNameIn = demandName[i + 1][j]
                    value[i][j] = self.api.ENgetdemandindex(j + 1, demandNameIn)
        else:
            self.api.errcode = 250
            self.api.ENgeterror()
        return value

    def get_NumeberNodeDemandCategories(self, *argv):
        """ Retrieves the value of all node base demands categorie number.
        """
        value = []
        if len(argv) > 0:
            index = argv[0]
            if isinstance(index, list):
                for i in index:
                    value.append(self.ep.ENgetnumdemands(i))
            else:
                value = self.ep.ENgetnumdemands(index)
        else:
            for i in range(self.get_NumNodes(0)):
                value.append(self.ep.ENgetnumdemands(i + 1))
        return value

    def get_nodeBaseDemand(self, *argv):
        indices = self.__getNodeIndices(*argv)
        numdemands = self.get_NumeberNodeDemandCategories(indices)
        value = {}
        val = np.zeros((max(numdemands), len(indices)))
        j = 1
        for i in indices:
            v = 0
            for u in range(numdemands[j - 1]):
                val[v][j - 1] = self.ep.ENgetbasedemand(i, u + 1)
                v += 1
            j += 1
        for i in range(max(numdemands)):
            value[i + 1] = np.array(val[i])
        return value

    def add_NodeDemand(self, *argv):
        nodeIndex = argv[0]
        baseDemand = argv[1]
        demandPattern = ''
        demandName = ''
        if len(argv) == 2:
            demandPattern = ''
            demandName = ''
        elif len(argv) == 3:
            demandPattern = argv[2]
            demandName = ''
        elif len(argv) == 4:
            demandPattern = argv[2]
            demandName = argv[3]
        if not isList(nodeIndex):
            self.ep.ENadddemand(nodeIndex, baseDemand, demandPattern, demandName)
        elif isList(nodeIndex) and not isList(baseDemand) and not isList(demandPattern) and not isList(demandName):
            for i in nodeIndex:
                self.ep.ENadddemand(i, baseDemand, demandPattern, demandName)
        elif isList(nodeIndex) and isList(baseDemand) and not isList(demandPattern) and not isList(demandName):
            for i in range(len(nodeIndex)):
                self.ep.ENadddemand(nodeIndex[i], baseDemand[i], demandPattern, demandName)
        elif isList(nodeIndex) and isList(baseDemand) and isList(demandPattern) and not isList(demandName):
            for i in range(len(nodeIndex)):
                self.ep.ENadddemand(nodeIndex[i], baseDemand[i], demandPattern[i], demandName)
        elif isList(nodeIndex) and isList(baseDemand) and isList(demandPattern) and isList(demandName):
            for i in range(len(nodeIndex)):
                self.ep.ENadddemand(nodeIndex[i], baseDemand[i], demandPattern[i], demandName[i])

        if isList(nodeIndex) and not isList(demandName):
            demandName = [demandName for _ in nodeIndex]

        return self.get_NodeJunctionDemandIndex(nodeIndex, demandName)


    def demand_model_summary(self):
        """
        Print information related to the current demand model
        """
        dm_type, pmin, preq, pexp = self.ep.ENgetdemandmodel()
        if dm_type == 0:
            print("Running a demand driven analysis...")
        else:
            print("Running a pressure driven analysis...")
            print("-> Minimum pressure: {:.2f}".format(pmin))
            print("-> Required pressure: {:.2f}".format(preq))
            print("-> Exponential pressure: {:.2f}".format(pexp))

    def __controlSet(self, value):
        splitRule = value.split()
        try:
            setting = self.TYPESTATUS.index(splitRule[2])
        except:
            if splitRule[2] == 'CLOSED':
                setting = 0
            else:
                setting = float(splitRule[2])
        lindex= self.ep.ENgetlinkindex(splitRule[1])
        ctype = 0
        nindex = 0
        level = 0

        if not lindex:
            raise Exception('Wrong link ID.')

        if splitRule[3] == 'IF':
            nindex = self.ep.ENgetnodeindex(splitRule[5])
            ctype = 0
            if splitRule[6] == 'ABOVE':
                ctype = 1
            level = float(splitRule[7])

        if splitRule[3] == 'AT':
            if splitRule[4] == 'CLOCKTIME':
                # LINK linkID status AT CLOCKTIME clocktime AM/PM
                nindex = 0
                ctype = 3
            else:
                # LINK linkID status AT TIME time
                nindex = 0
                ctype = 2
            if ':' not in splitRule[5]:
                level = int(splitRule[5])
            else:
                time_ = splitRule[5].split(':')
                level = int(time_[0]) * 3600 + int(time_[1]) * 60
        return [ctype,lindex,setting,nindex,level]

    def __addControlFunct(self, value):
        if isList(value):
            controlRuleIndex = []
            for c in value:
                [ctype,lindex,setting,nindex,level] = self.__controlSet(c)
                controlRuleIndex.append(self.ep.ENaddcontrol(ctype,lindex,setting,nindex,level))
        else:
            [ctype,lindex,setting,nindex,level] = self.__controlSet(value)
            controlRuleIndex = self.ep.ENaddcontrol(ctype,lindex,setting,nindex,level)
        return controlRuleIndex
    def __getNodeIndices(self, *argv):
        if len(argv) > 0:
            if isinstance(argv[0], list):
                if isinstance(argv[0][0], str):
                    return self.get_NodeIndex(argv[0])
                else:
                    return argv[0]
            else:
                if isinstance(argv[0], str):
                    return [self.get_NodeIndex(argv[0])]
                else:
                    return [argv[0]]
        else:
            return self.get_NodeIndex()

    def __getNodeJunctionIndices(self, *argv):
        if len(argv) == 0:
            numJuncs = self.get_NumNodes()
            return list(range(1, numJuncs + 1))
        else:
            return argv[0]

    def __setNodeDemandPattern(self, fun, propertyCode, value, *argv):

        categ = 1
        indices = self.__getNodeJunctionIndices()
        param = value
        if len(argv) == 2:
            indices = value
            categ = argv[0]
            param = argv[1]
        elif len(argv) == 1:
            indices = value
            param = argv[0]

        for c in range(categ):
            if len(argv) == 0 and type(value) is dict:
                param = value[c]
            j = 0
            resInd = self.get_NodeReservoirIndex()
            if not isList(indices):
                indices = [indices]
            if not isList(param):
                param = [param]
            for i in indices:
                if i in resInd:
                    if c + 1 > self.get_NumeberNodeDemandCategories(i):
                        self.add_NodeJunctionDemand(i, param[j])
                    else:
                        eval('self.api.' + fun + '(i, c, param[j])')
                elif categ == 1:
                    self.ep.ENsetnodevalue(i, propertyCode, param[j])
                else:
                    eval('self.api.' + fun + '(i, categ, param[j])')
                j += 1

    def add_control(self, ctype, *argv):
        """ Add a simple control.

        :param control: New Control
        :type ctype: float or list
        :return: Control index
        :rtype: int

        Example:
        index = net.add_control('LINK P1 CLOSED IF NODE N1 ABOVE 40')

        """
        if type(ctype) is dict:
            index = []
            for key in ctype:
                index.append(self.__addControlFunct(ctype[key]))
        else:
            if len(argv) == 0:
                index = self.__addControlFunct(ctype)
            else:
                lindex = argv[0]
                setting = argv[1]
                nindex = argv[2]
                level = argv[3]
                index = self.ep.ENaddcontrol(ctype,lindex,setting,nindex,level)
        return index
