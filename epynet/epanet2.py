##
# @mainpage EPYNET Python EpanetToolkit interface
#

##
# @file epanet2.py

import ctypes
import platform
import datetime
import os
import warnings


class EPANET2(object):

    def __init__(self, charset='UTF8'):
        _plat = platform.system()
        if _plat == 'Darwin':
            dll_path = os.path.join(os.path.dirname(__file__), "lib/libepanet.dylib")
            self._lib = ctypes.cdll.LoadLibrary(dll_path)
            ctypes.c_float = ctypes.c_double
        elif _plat == 'Linux':
            dll_path = os.path.join(os.path.dirname(__file__), "lib/libepanet.so")
            self._lib = ctypes.CDLL(dll_path)
            ctypes.c_float = ctypes.c_double
        elif _plat == 'Windows':
            ctypes.c_float = ctypes.c_double
            try:
                # if epanet2.dll compiled with __cdecl (as in OpenWaterAnalytics)
                dll_path = os.path.join(os.path.dirname(__file__), "lib/epanet2.dll")
                self._lib = ctypes.CDLL(dll_path)
            except ValueError:
                # if epanet2.dll compiled with __stdcall (as in EPA original DLL)
                try:
                    self._lib = ctypes.windll.epanet2
                    self._lib.EN_getversion(self.ph, ctypes.byref(ctypes.c_int()))
                except ValueError:
                    raise Exception("epanet2.dll not suitable")

        else:
            raise Exception('Platform ' + _plat + ' unsupported (not yet)')

        self.charset = charset
        self._current_simulation_time = ctypes.c_long()

        self.ph = ctypes.c_void_p()
        self._lib.EN_createproject.argtypes = [ctypes.c_void_p]
        self._lib.EN_createproject(ctypes.byref(self.ph))

        self._max_label_len = 32
        self._err_max_char = 80
        self.TYPENODE = self.TYPENODE = ['JUNCTION', 'RESERVOIR', 'TANK']
        self.Solve=0
    # Project Functions

    def ENclose(self):
        """! Closes a project and frees all of its memory."""
        ierr = self._lib.EN_close(self.ph)
        if ierr != 0:
            raise ENtoolkitError(self, ierr)

    def ENdeleteproject(self):
        """! Closes down the Toolkit system (including all files being processed)"""
        ierr = self._lib.EN_deleteproject(ctypes.byref(self.ph))
        if ierr != 0:
            raise ENtoolkitError(self, ierr)

    def ENgetcount(self, countcode):
        """Retrieves the number of network components of a specified type.

        Arguments:
        countcode: component code EN_NODECOUNT
                                  EN_TANKCOUNT
                                  EN_LINKCOUNT
                                  EN_PATCOUNT
                                  EN_CURVECOUNT
                                  EN_CONTROLCOUNT"""
        j = ctypes.c_int()
        ierr = self._lib.EN_getcount(self.ph, countcode, ctypes.byref(j))
        if ierr != 0:
            raise ENtoolkitError(self, ierr)
        return j.value

    def ENinit(self, rptfile, binfile, units_code, headloss_code):
        ierr = self._lib.EN_init(self.ph, ctypes.c_char_p(rptfile), ctypes.c_char_p(binfile), ctypes.c_int(units_code),
                                 ctypes.c_int(headloss_code))
        if ierr != 0:
            raise ENtoolkitError(self, ierr)

    def ENopen(self, nomeinp, nomerpt='', nomebin=''):
        """Opens the Toolkit to analyze a particular distribution system

        Arguments:
        nomeinp: name of the input file
        nomerpt: name of an output report file
        nomebin: name of an optional binary output file
        """
        ierr = self._lib.EN_open(self.ph, ctypes.c_char_p(nomeinp.encode()),
                                 ctypes.c_char_p(nomerpt.encode()),
                                 ctypes.c_char_p(nomebin.encode()))
        if ierr != 0:
            raise ENtoolkitError(self, ierr)

    def ENrunproject(self, nomeinp, nomerpt='', nomebin='', vfunc=None):
        """Runs a complete EPANET simulation.

        Arguments:
        nomeinp: name of the input file
        nomerpt: name of an output report file
        nomebin: name of an optional binary output file
        vfunc  : pointer to a user-supplied function which accepts a character string as its argument."""
        if vfunc is not None:
            CFUNC = ctypes.CFUNCTYPE(ctypes.c_void_p, ctypes.c_char_p)
            callback = CFUNC(vfunc)
        else:
            callback = None
        ierr = self._lib.EN_runproject(self.ph, ctypes.c_char_p(nomeinp.encode()),
                                       ctypes.c_char_p(nomerpt.encode()),
                                       ctypes.c_char_p(nomebin.encode()),
                                       callback)
        if ierr != 0:
            raise ENtoolkitError(self, ierr)

    def ENsaveinpfile(self, fname):
        """Writes all current network input data to a file
        using the format of an EPANET input file.

         ENsaveinpfile(inpname)
        """
        ierr = self._lib.EN_saveinpfile(self.ph, ctypes.c_char_p(fname.encode()))
        if ierr != 0:
            raise ENtoolkitError(self, ierr)

    # Hydraulic Analysis Functions

    def ENcloseH(self):
        """Closes the hydraulic analysis system, freeing all allocated memory."""
        ierr = self._lib.EN_closeH(self.ph)
        if ierr != 0:
            raise ENtoolkitError(self, ierr)

    def ENinitH(self, flag=None):
        """Initializes storage tank levels, link status and settings,
            and the simulation clock time prior
            to running a hydraulic analysis.

            flag  EN_NOSAVE [+EN_SAVE] [+EN_INITFLOW] """
        ierr = self._lib.EN_initH(self.ph, flag)
        if ierr != 0:
            raise ENtoolkitError(self, ierr)

    def ENnextH(self):
        """Determines the length of time until the next hydraulic event occurs in an extended period
           simulation."""
        _deltat = ctypes.c_long()
        ierr = self._lib.EN_nextH(self.ph, ctypes.byref(_deltat))
        if ierr != 0:
            raise ENtoolkitError(self, ierr)
        return _deltat.value

    def ENopenH(self):
        """Opens the hydraulics analysis system"""
        ierr = self._lib.EN_openH(self.ph, )

    def ENrunH(self):
        """Runs a single period hydraulic analysis,
            retrieving the current simulation clock time t"""
        ierr = self._lib.EN_runH(self.ph, ctypes.byref(self._current_simulation_time))
        if ierr >= 100:
            raise ENtoolkitError(self, ierr)
        elif ierr > 0:
            warnings.warn(self.ENgeterror(ierr))
            return self.ENgeterror(ierr)

    def ENsaveH(self):
        """Transfers results of a hydraulic simulation
        from the binary Hydraulics file to the binary
        Output file, where results are only reported at
        uniform reporting intervals."""
        ierr = self._lib.EN_saveH(self.ph, )
        if ierr != 0:
            raise ENtoolkitError(self, ierr)

    def ENsavehydfile(self, fname):
        """Saves the current contents of the binary hydraulics file to a file.
            ARGUMENTS:
                fname	the name of the file to be created

        Use this function to save the current set of hydraulics results to a file, either for post-processing
        or to be used at a later time by calling the EN_usehydfile function.

        The hydraulics file contains nodal demands and heads and link flows, status, and settings for all hydraulic time
        steps,even intermediate ones.

        Before calling this function hydraulic results must have been generated and saved by having called EN_solveH or
        the EN_initH - EN_runH - EN_nextH sequence with the initflag argument of EN_initH set to EN_SAVE or
        EN_SAVE_AND_INIT.
        """
        ierr = self._lib.EN_savehydfile(self.ph, ctypes.c_char_p(fname.encode()))
        if ierr != 0:
            raise ENtoolkitError(self, ierr)

    def ENsolveH(self):
        """Runs a complete hydraulic simulation with results
        for all time periods written to the binary Hydraulics file.

        Use EN_solveH to generate a complete hydraulic solution which can stand alone or be used as input
        to a water quality analysis. This function will not allow one to examine intermediate hydraulic results
        as they are generated. It can also be followed by calls to EN_saveH and EN_report to write hydraulic results
        to the report file.

        The sequence EN_openH - EN_initH - EN_runH - EN_nextH - EN_closeH can be used instead to gain access to results
        at intermediate time periods and directly adjust link status and control settings as a simulation proceeds.
        """
        ierr = self._lib.EN_solveH(self.ph)
        if ierr != 0:
            raise ENtoolkitError(self, ierr)

    def ENusehydfile(self, fname):
        """Uses the contents of the specified file as the current binary hydraulics file

        ARGUMENTS:
            fname	the name of the binary file containing hydraulic results."""
        ierr = self._lib.EN_usehydfile(self.ph, ctypes.c_char_p(fname.encode()))
        if ierr != 0:
            raise ENtoolkitError(self, ierr)

    # Water Quality Analysis Functions

    def ENcloseQ(self):
        """Closes the water quality analysis system,
        freeing all allocated memory."""
        ierr = self._lib.EN_closeQ(self.ph)
        if ierr != 0:
            raise ENtoolkitError(self, ierr)

    def ENinitQ(self, flag=None):
        """Initializes water quality and the simulation clock
        time prior to running a water quality analysis.

        flag  EN_NOSAVE | EN_SAVE """
        ierr = self._lib.EN_initQ(self.ph, flag)
        if ierr != 0:
            raise ENtoolkitError(self, ierr)

    def ENnextQ(self):
        """Advances the water quality simulation
        to the start of the next hydraulic time period."""
        _deltat = ctypes.c_long()
        ierr = self._lib.EN_nextQ(self.ph, ctypes.byref(_deltat))
        if ierr != 0:
            raise ENtoolkitError(self, ierr)
        return _deltat.value

    def ENopenQ(self):
        """Opens the water quality analysis system"""
        ierr = self._lib.EN_openQ(self.ph, )

    def ENrunQ(self):
        """Makes available the hydraulic and water quality results
        that occur at the start of the next time period of a water quality analysis,
        where the start of the period is returned in t."""
        ierr = self._lib.EN_runQ(self.ph, ctypes.byref(self._current_simulation_time))
        if ierr >= 100:
            raise ENtoolkitError(self, ierr)
        elif ierr > 0:
            return self.ENgeterror(ierr)

    def ENsolveQ(self):
        """Runs a complete water quality simulation with results
        at uniform reporting intervals written to EPANET's binary Output file."""
        ierr = self._lib.EN_solveQ(self.ph, )
        if ierr != 0:
            raise ENtoolkitError(self, ierr)

    def ENstepQ(self):
        """Advances the water quality simulation one water quality time step.
        The time remaining in the overall simulation is returned in tleft."""
        tleft = ctypes.c_long()
        ierr = self._lib.EN_nextQ(self.ph, ctypes.byref(tleft))
        if ierr != 0:
            raise ENtoolkitError(self, ierr)
        return tleft.value

    def ENsetqualtype(self, qualcode, chemname, chemunits, tracenode):
        """Sets the type of water quality analysis called for.

        Arguments:
             qualcode:	water quality analysis code
             chemname:	name of the chemical being analyzed
             chemunits:	units that the chemical is measured in
             tracenode:	ID of node traced in a source tracing analysis """
        ierr = self._lib.EN_setqualtype(self.ph, ctypes.c_int(qualcode),
                                        ctypes.c_char_p(chemname.encode(self.charset)),
                                        ctypes.c_char_p(chemunits.encode(self.charset)),
                                        ctypes.c_char_p(tracenode.encode(self.charset)))
        if ierr != 0:
            raise ENtoolkitError(self, ierr)

    # Reporting Functions

    def ENgeterror(self, errcode):
        """Retrieves the text of the message associated with a particular error or warning code."""
        errmsg = ctypes.create_string_buffer(self._err_max_char)
        self._lib.ENgeterror(errcode, ctypes.byref(errmsg), self._err_max_char)
        return errmsg.value.decode(self.charset)

    def ENgetversion(self):
        """Retrieves the current version number of the Toolkit."""
        j = ctypes.c_int()
        ierr = self._lib.EN_getversion(self.ph, ctypes.byref(j))
        if ierr != 0:
            raise ENtoolkitError(self, ierr)
        return j.value

    def ENreport(self):
        """Writes a formatted text report on simulation results
        to the Report file."""
        ierr = self._lib.EN_report(self.ph, )
        if ierr != 0:
            raise ENtoolkitError(self, ierr)

    def ENsetreport(self, command):
        """Issues a report formatting command.

        Formatting commands are the same as used in the
        [REPORT] section of the EPANET Input file."""
        ierr = self._lib.EN_setreport(self.ph, ctypes.c_char_p(command.encode(self.charset)))
        if ierr != 0:
            raise ENtoolkitError(self, ierr)

    def ENresetreport(self):
        """Clears any report formatting commands

        that either appeared in the [REPORT] section of the
        EPANET Input file or were issued with the
        ENsetreport function"""
        ierr = self._lib.EN_resetreport(self.ph, )
        if ierr != 0:
            raise ENtoolkitError(self, ierr)

    def ENsetstatusreport(self, statuslevel):
        """Sets the level of hydraulic status reporting.

        statuslevel:  level of status reporting
                      0 - no status reporting
                      1 - normal reporting
                      2 - full status reporting"""
        ierr = self._lib.EN_setstatusreport(self.ph, ctypes.c_int(statuslevel))
        if ierr != 0:
            raise ENtoolkitError(self, ierr)

    def ENwriteline(self, line):
        """Writes a line of text to the EPANET report file.

          Arguments:
            line:	a text string to write """
        ierr = self._lib.EN_writeline(self.ph, ctypes.c_char_p(line.encode(self.charset)))
        if ierr != 0:
            raise ENtoolkitError(self, ierr)

    # Analysis Options Functions

    def ENgetflowunits(self):
        """Retrieves a code number indicating the units used to express all flow rates."""
        j = ctypes.c_int()
        ierr = self._lib.EN_getflowunits(self.ph, ctypes.byref(j))
        if ierr != 0:
            raise ENtoolkitError(self, ierr)
        return j.value

    def ENgetoption(self, optioncode):
        """Retrieves the value of a particular analysis option.

        Arguments:
        optioncode: EN_TRIALS
                    EN_ACCURACY
                    EN_TOLERANCE
                    EN_EMITEXPON
                    EN_DEMANDMULT"""
        j = ctypes.c_float()
        ierr = self._lib.EN_getoption(self.ph, optioncode, ctypes.byref(j))
        if ierr != 0:
            raise ENtoolkitError(self, ierr)
        return j.value

    def ENgetqualinfo(self):
        """Gets information about the type of water quality analysis requested.
        ARGUMENTS:
            [out]	qualType	    type of analysis to run (see EN_QualityType).
            [out]	out_chemName	name of chemical constituent.
            [out]	out_chemUnits	concentration units of the constituent.
            [out]	traceNode	    index of the node being traced (if applicable). """

        out_qualType = ctypes.c_int()
        out_chemName = ctypes.c_char()
        out_chemUnits = ctypes.c_char()
        out_traceNode = ctypes.c_int()

        ierr = self._lib.EN_getqualinfo(self.ph, ctypes.byref(out_qualType), ctypes.byref(out_chemName),
                                        ctypes.byref(out_chemUnits), ctypes.byref(out_traceNode))
        if ierr != 0:
            raise ENtoolkitError(self, ierr)
        return (out_qualType.value, out_chemName.value.decode(self.charset), out_chemUnits.value.decode(self.charset),
                out_traceNode.value)

    def ENgetqualtype(self):
        """Retrieves the type of water quality analysis called for
        returns  qualcode: Water quality analysis codes are as follows:
                           EN_NONE	0 No quality analysis
                           EN_CHEM	1 Chemical analysis
                           EN_AGE 	2 Water age analysis
                           EN_TRACE	3 Source tracing
                 tracenode:	index of node traced in a source tracing
                            analysis  (value will be 0 when qualcode
                            is not EN_TRACE)"""
        qualcode = ctypes.c_int()
        tracenode = ctypes.c_int()
        ierr = self._lib.EN_getqualtype(self.ph, ctypes.byref(qualcode),
                                        ctypes.byref(tracenode))
        if ierr != 0:
            raise ENtoolkitError(self, ierr)
        return qualcode.value, tracenode.value

    def ENgettimeparam(self, paramcode):
        """Retrieves the value of a specific analysis time parameter.
        Arguments:
        paramcode: EN_DURATION
                   EN_HYDSTEP
                   EN_QUALSTEP
                   EN_PATTERNSTEP
                   EN_PATTERNSTART
                   EN_REPORTSTEP
                   EN_REPORTSTART
                   EN_RULESTEP
                   EN_STATISTIC
                   EN_PERIODS"""
        j = ctypes.c_int()
        ierr = self._lib.EN_gettimeparam(self.ph, paramcode, ctypes.byref(j))
        if ierr != 0:
            raise ENtoolkitError(self, ierr)
        return j.value

    def ENsetflowunits(self, units):

        """ Sets a project's flow units.
        units: a flow units code
        FlowUnits = 0 = EN_CFS: "cfs",
                    1 = EN_GPM: "gpm",
                    2 = EN_MGD: "a-f/d",
                    3 = EN_IMGD: "mgd",
                    4 = EN_AFD: "Imgd",
                    5 = EN_LPS: "L/s",
                    6 = EN_LPM: "Lpm",
                    7 = EN_MLD: "m3/h",
                    8 = EN_CMH: "m3/d",
                    9 = EN_CMD: "ML/d",
                   10 = EN_CMS: "m3/s"
        """
        ierr = self._lib.EN_setflowunits(self.ph, ctypes.c_int(units))
        if ierr != 0:
            raise ENtoolkitError(self, ierr)

    def ENsetoption(self, optioncode, value):
        """Sets the value of a particular analysis option.

        Arguments:
          optioncode: option code EN_TRIALS
                                  EN_ACCURACY
                                  EN_TOLERANCE
                                  EN_EMITEXPON
                                  EN_DEMANDMULT
          value:  option value"""
        ierr = self._lib.EN_setoption(self.ph, ctypes.c_int(optioncode), ctypes.c_float(value))
        if ierr != 0:
            raise ENtoolkitError(self, ierr)

    def ENsettimeparam(self, paramcode, timevalue):
        """Sets the value of a time parameter.
        Arguments:
          paramcode: time parameter code 0 = EN_DURATION
                                         1 = EN_HYDSTEP
                                         2 = EN_QUALSTEP
                                         3 = EN_PATTERNSTEP
                                         4 = EN_PATTERNSTART
                                         5 = EN_REPORTSTEP
                                         6 = EN_REPORTSTART
                                         7 = EN_RULESTEP
                                         8 = EN_STATISTIC
                                         9 = EN_PERIODS
                                        10 = EN_STARTTIME
                                        11 = EN_HTIME
                                        12 = EN_QTIME
                                        13 = EN_HALTFLAG
                                        14 = EN_NEXTEVENT
                                        15 = EN_NEXTEVENTTANK

          timevalue: value of time parameter in seconds
                          The codes for EN_STATISTIC are:
                          EN_NONE     none
                          EN_AVERAGE  averaged
                          EN_MINIMUM  minimums
                          EN_MAXIMUM  maximums
                          EN_RANGE    ranges"""
        ierr = self._lib.EN_settimeparam(self.ph, ctypes.c_int(paramcode), ctypes.c_int(timevalue))
        if ierr != 0:
            raise ENtoolkitError(self, ierr)

    # Network Node Functions

    def ENdeletenode(self, node_index, conditional=0):
        ierr = self._lib.EN_deletenode(self.ph, ctypes.c_int(node_index), ctypes.c_int(conditional))
        if ierr != 0:
            raise ENtoolkitError(self, ierr)

    def ENaddnode(self, node_id, node_type_code):
        """ Adds a new node to a project.

        ENaddnode(nodeid, nodetype)

        Parameters:
        nodeid       the ID name of the node to be added.
        nodetype     the type of node being added.
                    0 = junction
                    1 = reservoir
                    2 = tank

        Returns:
        index    the index of the newly added node.
        See also EN_NodeProperty, NodeType
        """

        index = ctypes.c_int()

        ierr = self._lib.EN_addnode(self.ph, ctypes.c_char_p(node_id.encode(self.charset)),
                                    ctypes.c_int(node_type_code), ctypes.byref(index))
        if ierr != 0:
            raise ENtoolkitError(self, ierr)

        return index

    def ENgetcoord(self, index):
        """Retrieves the coordinates (x,y) for a specific node.

        Arguments:
        index: node index"""
        x = ctypes.c_float()
        y = ctypes.c_float()
        ierr = self._lib.EN_getcoord(self.ph, index, ctypes.byref(x), ctypes.byref(y))
        if ierr != 0:
            raise ENtoolkitError(self, ierr)
        return (x.value, y.value)

    def ENgetnodeid(self, index):
        """Retrieves the ID label of a node with a specified index.

        Arguments:
        index: node index"""
        label = ctypes.create_string_buffer(self._max_label_len)
        ierr = self._lib.EN_getnodeid(self.ph, index, ctypes.byref(label))
        if ierr != 0:
            raise ENtoolkitError(self, ierr)
        return label.value.decode(self.charset)

    def ENgetnodeindex(self, nodeid):
        """Retrieves the index of a node with a specified ID.

        Arguments:
        nodeid: node ID label"""
        j = ctypes.c_int()
        ierr = self._lib.EN_getnodeindex(self.ph, ctypes.c_char_p(nodeid.encode(self.charset)), ctypes.byref(j))
        if ierr != 0:
            raise ENtoolkitError(self, ierr)
        return j.value

    def ENgetnodetype(self, index):
        """Retrieves the node-type code for a specific node.

        Arguments:
        index: node index"""
        j = ctypes.c_int()
        ierr = self._lib.EN_getnodetype(self.ph, index, ctypes.byref(j))
        if ierr != 0:
            raise ENtoolkitError(self, ierr)
        return j.value

    # def ENgetnodevalue(self, index, paramcode):
    #     """Retrieves the value of a specific node parameter.

    #     Arguments:
    #     index:     node index
    #     paramcode: Node parameter codes consist of the following constants:
    #                   EN_ELEVATION  Elevation
    #                   EN_BASEDEMAND ** Base demand
    #                   EN_PATTERN    ** Demand pattern index
    #                   EN_EMITTER    Emitter coeff.
    #                   EN_INITQUAL   Initial quality
    #                   EN_SOURCEQUAL Source quality
    #                   EN_SOURCEPAT  Source pattern index
    #                   EN_SOURCETYPE Source type (See note below)
    #                   EN_TANKLEVEL  Initial water level in tank
    #                   EN_DEMAND     * Actual demand
    #                   EN_HEAD       * Hydraulic head
    #                   EN_PRESSURE   * Pressure
    #                   EN_QUALITY    * Actual quality
    #                   EN_SOURCEMASS * Mass flow rate per minute of a chemical source
    #                     * computed values)
    #                    ** primary demand category is last on demand list

    #                The following parameter codes apply only to storage tank nodes:
    #                   EN_INITVOLUME  Initial water volume
    #                   EN_MIXMODEL    Mixing model code (see below)
    #                   EN_MIXZONEVOL  Inlet/Outlet zone volume in a 2-compartment tank
    #                   EN_TANKDIAM    Tank diameter
    #                   EN_MINVOLUME   Minimum water volume
    #                   EN_VOLCURVE    Index of volume versus depth curve (0 if none assigned)
    #                   EN_MINLEVEL    Minimum water level
    #                   EN_MAXLEVEL    Maximum water level
    #                   EN_MIXFRACTION Fraction of total volume occupied by the inlet/outlet zone in a 2-compartment tank
    #                   EN_TANK_KBULK  Bulk reaction rate coefficient"""
    #     j = ctypes.c_double()
    #     ierr = self._lib.EN_getnodevalue(self.ph, index, paramcode, ctypes.byref(j))
    #     if ierr != 0:
    #         raise ENtoolkitError(self, ierr)
    #     return j.value

    import ctypes

    def ENgetnodevalue(self, index, paramcode):
        """Retrieves the value of a specific node parameter."""

        value = ctypes.c_double()
        ierr = self._lib.EN_getnodevalue(self.ph, int(index), paramcode, ctypes.byref(value))

        if ierr == 240:
            return None  # Return None explicitly for undefined values (error 240)
        elif ierr != 0:
                raise ENtoolkitError(self, ierr)  # Raise specific error for other codes

        return value.value


    def ENsetcoord(self, index, x, y):
        ierr = self._lib.EN_setcoord(self.ph, ctypes.c_int(index),
                                     ctypes.c_float(x),
                                     ctypes.c_float(y))
        if ierr != 0:
            raise ENtoolkitError(self, ierr)

    def ENsetnodevalue(self, index, paramcode, value):
        """Sets the value of a parameter for a specific node.
        Arguments:
        index:  node index
        paramcode: Node parameter codes consist of the following constants:
                      EN_ELEVATION  Elevation
                      EN_BASEDEMAND ** Base demand
                      EN_PATTERN    ** Demand pattern index
                      EN_EMITTER    Emitter coeff.
                      EN_INITQUAL   Initial quality
                      EN_SOURCEQUAL Source quality
                      EN_SOURCEPAT  Source pattern index
                      EN_SOURCETYPE Source type (See note below)
                      EN_TANKLEVEL  Initial water level in tank
                           ** primary demand category is last on demand list
                   The following parameter codes apply only to storage tank nodes
                      EN_TANKDIAM      Tank diameter
                      EN_MINVOLUME     Minimum water volume
                      EN_MINLEVEL      Minimum water level
                      EN_MAXLEVEL      Maximum water level
                      EN_MIXMODEL      Mixing model code
                      EN_MIXFRACTION   Fraction of total volume occupied by the inlet/outlet
                      EN_TANK_KBULK    Bulk reaction rate coefficient
        value:parameter value"""
        ierr = self._lib.EN_setnodevalue(self.ph, ctypes.c_int(index), ctypes.c_int(paramcode), ctypes.c_double(value))
        if ierr != 0:
            raise ENtoolkitError(self, ierr)

    def ENsettankdata(self, index, elev, initlvl, minlvl, maxlvl, diam, minvol, volcur):
        """Sets a group of properties for a tank node.
        Arguments:

                    index	 : a tank node's index (starting from 1).
                    elev	 : the tank's bottom elevation.
                    initlvl	 : the initial water level in the tank.
                    minlvl	 : the minimum water level for the tank.
                    maxlvl	 : the maximum water level for the tank.
                    diam	 : the tank's diameter (0 if a volume curve is supplied).
                    minvol	 : the volume of the tank at its minimum water level.
                    volcur : the name of the tank's volume curve ("" for no curve)

        """
        ierr = self._lib.EN_settankdata(self.ph, ctypes.c_int(index), ctypes.c_float(elev), ctypes.c_float(initlvl)
                                        , ctypes.c_float(minlvl), ctypes.c_float(maxlvl), ctypes.c_float(diam),
                                        ctypes.c_float(minvol)
                                        , ctypes.c_char_p(volcur.encode(self.charset)))
        if ierr != 0:
            raise ENtoolkitError(self, ierr)

    # Nodal Demand Functions
    def ENadddemand(self, index, baseDemand, demandPattern, demandName):
        """ Appends a new demand to a junction node demands list.

        ENadddemand(index, baseDemand, demandPattern, demandName)

        Parameters:
        index            the index of a node (starting from 1).
        baseDemand       the demand's base value.
        demandPattern    the name of a time pattern used by the demand.
        demandName       the name of the demand's category.

            http://wateranalytics.org/EPANET/group___demands.html
        """
        ierr = self._lib.EN_adddemand(self.ph, ctypes.c_int(index), ctypes.c_float(baseDemand),
                                      ctypes.c_char_p(demandPattern.encode(self.charset)),
                                      ctypes.c_char_p(demandName.encode(self.charset)))

        if ierr != 0:
            raise ENtoolkitError(self, ierr)

    def ENdeletedemand(self, index, demandindex):
        """ deletes a demand from a junction node.

        ENdeletedemand(index, demandIndex)

        Arguments:
        index:          the index of a node (starting from 1).
        demandindex :   the position of the demand in the node's demands list (starting from 1).
        """

        ierr = self._lib.EN_deletedemand(self.ph, ctypes.c_int(index), ctypes.c_int(demandindex))
        if ierr != 0:
            raise ENtoolkitError(self, ierr)

    def ENgetbasedemand(self, index, demandindex):
        """ Gets the base demand for one of a node's demand categories.
                Arguments:
                index: a node's index (starting from 1).
                demandindex : the index of a demand category for the node (starting from 1).
                """
        label = ctypes.create_string_buffer(self._max_label_len)
        ierr = self._lib.EN_getbasedemand(self.ph, ctypes.c_int(index), ctypes.c_int(demandindex))
        if ierr != 0:
            raise ENtoolkitError(self, ierr)
        return label.value.decode(self.charset)

    def ENgetdemandname(self, index, demandindex):
        """Retrieves the name of a node's demand category.

        Arguments:
        index: node index
        demandindex: demandindex
        """

        label = ctypes.create_string_buffer(self._max_label_len)
        ierr = self._lib.EN_getdemandname(self.ph, index, demandindex, ctypes.byref(label))
        if ierr != 0:
            raise ENtoolkitError(self, ierr)
        return label.value.decode(self.charset)

    def ENgetnumdemands(self, index):

        """Retrieves the number of demand categories for a junction node.

        Arguments:
        index: node index"""

        j = ctypes.c_int()
        ierr = self._lib.EN_getnumdemands(self.ph, index, ctypes.byref(j))
        if ierr != 0:
            raise ENtoolkitError(self, ierr)
        return j.value
    def ENgetdemandmodel(self):
        """
        Retrieves the type of demand model in use and its parameters.
        :returns dm_type: type of demand model (DDA or PDA)
                 pmin:    pressure below which there is no demand
                 preq:    pressure required to deliver full demand
                 pexp:    pressure exponent in demand function
        """
        dm_type = ctypes.c_int()
        pmin = ctypes.c_float()
        preq = ctypes.c_float()
        pexp = ctypes.c_float()
        ierr = self._lib.EN_getdemandmodel(self.ph,
                                           ctypes.byref(dm_type),
                                           ctypes.byref(pmin),
                                           ctypes.byref(preq),
                                           ctypes.byref(pexp))
        if ierr != 0:
            raise ENtoolkitError(self, ierr)
        return dm_type.value, pmin.value, preq.value, pexp.value

    def ENsetdemandmodel(self, dm_type, pmin, preq, pexp):
        """
        Sets the type of demand model to use and its parameters
        :param dm_type: type of demand model (DDA or PDA)
        :param pmin: pressure below which there is no demand
        :param preq: pressure required to deliver full demand
        :param pexp: pressure exponent in demand function
        """
        ierr = self._lib.EN_setdemandmodel(self.ph,
                                           ctypes.c_int(dm_type),
                                           ctypes.c_float(pmin),
                                           ctypes.c_float(preq),
                                           ctypes.c_float(pexp))
        if ierr != 0:
            raise ENtoolkitError(self, ierr)


    # Network Link Functions

    def ENdeletelink(self, link_index, conditional=0):
        ierr = self._lib.EN_deletelink(self.ph, ctypes.c_int(link_index), ctypes.c_int(conditional))
        if ierr != 0:
            raise ENtoolkitError(self, ierr)

    def ENgetheadcurveindex(self, pump_index):
        j = ctypes.c_int()
        ierr = self._lib.EN_getheadcurveindex(self.ph, ctypes.c_int(pump_index), ctypes.byref(j))
        if ierr != 0:
            raise ENtoolkitError(self, ierr)
        return j.value

    def ENgetlinkid(self, index):
        """Retrieves the ID label of a link with a specified index.

        Arguments:
        index: link index"""
        label = ctypes.create_string_buffer(self._max_label_len)
        ierr = self._lib.EN_getlinkid(self.ph, index, ctypes.byref(label))
        if ierr != 0:
            raise ENtoolkitError(self, ierr)
        return label.value.decode(self.charset)

    def ENgetlinknodes(self, index):
        """Retrieves the indexes of the end nodes of a specified link.

        Arguments:
        index: link index"""
        j1 = ctypes.c_int()
        j2 = ctypes.c_int()
        ierr = self._lib.EN_getlinknodes(self.ph, index, ctypes.byref(j1), ctypes.byref(j2))
        if ierr != 0:
            raise ENtoolkitError(self, ierr)
        return j1.value, j2.value

    def ENgetvertex(self, index, vertex):
        """ Retrieves the coordinate's of a vertex point assigned to a link.


        ENgetvertex(index, vertex)

        Parameters:
        index      a link's index (starting from 1).
        vertex     a vertex point index (starting from 1).

        Returns:
        x  the vertex's X-coordinate value.
        y  the vertex's Y-coordinate value.
        """
        x = ctypes.c_double()  # need double for EN_ or EN functions.
        y = ctypes.c_double()
        if self.ph is not None:
            ierr = self._lib.EN_getvertex(self.ph, int(index), vertex, ctypes.byref(x), ctypes.byref(y))
        else:
            ierr = self._lib.ENgetvertex(int(index), vertex, ctypes.byref(x), ctypes.byref(y))

        if ierr != 0:
            raise ENtoolkitError(self, ierr)
        return [x.value, y.value]

    def ENgetvertexcount(self, index):  
        """ Retrieves the number of internal vertex points assigned to a link.

        ENgetvertexcount(index)

        Parameters:
        index      a link's index (starting from 1).

        Returns:
        count  the number of vertex points that describe the link's shape.
        """
        count = ctypes.c_int()

        if self.ph is not None:
            ierr = self._lib.EN_getvertexcount(self.ph, int(index),ctypes.byref(count))
        else:
            ierr = self._lib.ENgetvertexcount(int(index), ctypes.byref(count))

        if ierr != 0:
            raise ENtoolkitError(self, ierr)
        return count.value

    def ENgetlinktype(self, index):
        """Retrieves the link-type code for a specific link.

        Arguments:
        index: link index"""
        j = ctypes.c_int()
        ierr = self._lib.EN_getlinktype(self.ph, index, ctypes.byref(j))
        if ierr != 0:
            raise ENtoolkitError(self, ierr)
        return j.value

    def ENgetlinkvalue(self, index, paramcode):
        """Retrieves the value of a specific link parameter.

        Arguments:
        index:     link index
        paramcode: Link parameter codes consist of the following constants:
                     EN_DIAMETER     Diameter
                     EN_LENGTH       Length
                     EN_ROUGHNESS    Roughness coeff.
                     EN_MINORLOSS    Minor loss coeff.
                     EN_INITSTATUS   Initial link status (0 = closed, 1 = open)
                     EN_INITSETTING  Roughness for pipes, initial speed for pumps, initial setting for valves
                     EN_KBULK        Bulk reaction coeff.
                     EN_KWALL        Wall reaction coeff.
                     EN_FLOW         * Flow rate
                     EN_VELOCITY     * Flow velocity
                     EN_HEADLOSS     * Head loss
                     EN_STATUS       * Actual link status (0 = closed, 1 = open)
                     EN_SETTING      * Roughness for pipes, actual speed for pumps, actual setting for valves
                     EN_ENERGY       * Energy expended in kwatts
                       * computed values"""
        j = ctypes.c_float()
        ierr = self._lib.EN_getlinkvalue(self.ph, index, paramcode, ctypes.byref(j))
        if ierr != 0:
            raise ENtoolkitError(self, ierr)
        return j.value

    def ENgetlinkindex(self, linkid):
        """Retrieves the index of a link with a specified ID.

        Arguments:
        linkid: link ID label"""
        j = ctypes.c_int()
        ierr = self._lib.EN_getlinkindex(self.ph, ctypes.c_char_p(linkid.encode(self.charset)), ctypes.byref(j))
        if ierr != 0:
            raise ENtoolkitError(self, ierr)
        return j.value

    def ENsetheadcurveindex(self, pump_index, curve_index):
        ierr = self._lib.EN_setheadcurveindex(self.ph, ctypes.c_int(pump_index), ctypes.c_int(curve_index))
        if ierr != 0:
            raise ENtoolkitError(self, ierr)

    def ENaddlink(self, link_id, link_type_code, from_node_id, to_node_id):

        index = ctypes.c_int()

        ierr = self._lib.EN_addlink(self.ph, ctypes.c_char_p(link_id.encode(self.charset)),
                                    ctypes.c_int(link_type_code), ctypes.c_char_p(from_node_id.encode(self.charset)),
                                    ctypes.c_char_p(to_node_id.encode(self.charset)), ctypes.byref(index))
        if ierr != 0:
            raise ENtoolkitError(self, ierr)

    def ENsetlinktype(self, indexLink, linkType):
        """ Changes link type.
        Arguments:
        indexLink:  	The link's index.
        linkType:       The new type to change the link to
            0 = EN_CVPIPE 	Pipe with check valve.
            1 = EN_PIPE 	Pipe.
            2 = EN_PUMP 	Pump.
            3 = EN_PRV 	    Pressure reducing valve.
            4 = EN_PSV 	    Pressure sustaining valve.
            5 = EN_PBV      Pressure breaker valve.
            6 = EN_FCV      Flow control valve
            7 = EN_TCV      Throttle control valve.
            8 = EN_GPV      General purpose valve.
        """
        indexLink = ctypes.c_int(indexLink)
        self.errcode = self._lib.EN_setlinktype(self.ph, ctypes.byref(indexLink), linkType, 0)
        # self.ENgeterror()
        return indexLink.value

    def ENsetlinkvalue(self, index, paramcode, value):
        """Sets the value of a parameter for a specific link.
        Arguments:
        index:  link index
        paramcode: Link parameter codes consist of the following constants:
                     EN_DIAMETER     Diameter
                     EN_LENGTH       Length
                     EN_ROUGHNESS    Roughness coeff.
                     EN_MINORLOSS    Minor loss coeff.
                     EN_INITSTATUS   * Initial link status (0 = closed, 1 = open)
                     EN_INITSETTING  * Roughness for pipes, initial speed for pumps, initial setting for valves
                     EN_KBULK        Bulk reaction coeff.
                     EN_KWALL        Wall reaction coeff.
                     EN_STATUS       * Actual link status (0 = closed, 1 = open)
                     EN_SETTING      * Roughness for pipes, actual speed for pumps, actual setting for valves
                     * Use EN_INITSTATUS and EN_INITSETTING to set the design value for a link's status or setting that
                       exists prior to the start of a simulation. Use EN_STATUS and EN_SETTING to change these values while
                       a simulation is being run (within the ENrunH - ENnextH loop).

        value:parameter value"""
        ierr = self._lib.EN_setlinkvalue(self.ph, ctypes.c_int(index),
                                         ctypes.c_int(paramcode),
                                         ctypes.c_float(value))
        if ierr != 0:
            raise ENtoolkitError(self, ierr)


    def ENsetvertices(self, index, x, y, vertex):
        """ Assigns a set of internal vertex points to a link.


        ENsetvertices(index, x, y, vertex)

        Parameters:
        index      a link's index (starting from 1).
        x          an array of X-coordinates for the vertex points.
        y          an array of Y-coordinates for the vertex points.
        vertex     the number of vertex points being assigned.
        """

        if self.ph is not None:
            ierr = self._lib.EN_setvertices(self.ph, int(index), (ctypes.c_double * vertex)(*x),
                                                    (ctypes.c_double * vertex)(*y), vertex)

        else:
            ierr = self._lib.ENsetvertices(int(index), (ctypes.c_double * vertex)(*x),
                                                   (ctypes.c_double * vertex)(*y), vertex)

        if ierr != 0:
            raise ENtoolkitError(self, ierr)
    

    # Time Pattern Functions.

    def ENdeletepattern(self, index):
        """Deletes a time pattern from a project.

        Arguments:
        index: pattern index"""

        label = ctypes.create_string_buffer(self._max_label_len)
        ierr = self._lib.EN_deletepattern(self.ph, index, ctypes.byref(label))
        if ierr != 0:
            raise ENtoolkitError(self, ierr)
        return label.value.decode(self.charset)

    def ENgetaveragepatternvalue(self, index):
        """Retrieves the average of all pattern factors in a time pattern.

                        Arguments:
                        index	a time pattern index (starting from 1).
                        [out]	value	The average of all of the time pattern's factors."""

        j = ctypes.c_int()
        ierr = self._lib.EN_getaveragepatternvalue(self.ph, index, ctypes.byref(j))
        if ierr != 0:
            raise ENtoolkitError(self, ierr)
        return j.value

    def ENgetpatternid(self, index):
        """Retrieves the ID label of a particular time pattern.

        Arguments:
        index: pattern index"""
        label = ctypes.create_string_buffer(self._max_label_len)
        ierr = self._lib.EN_getpatternid(self.ph, index, ctypes.byref(label))
        if ierr != 0:
            raise ENtoolkitError(self, ierr)
        return label.value.decode(self.charset)

    def ENgetpatternindex(self, patternid):
        """Retrieves the index of a particular time pattern.

        Arguments:
        id: pattern ID label"""
        j = ctypes.c_int()
        ierr = self._lib.EN_getpatternindex(self.ph, ctypes.c_char_p(patternid.encode(self.charset)), ctypes.byref(j))
        if ierr != 0:
            raise ENtoolkitError(self, ierr)
        return j.value

    def ENgetpatternlen(self, index):
        """Retrieves the number of time periods in a specific time pattern.

        Arguments:
        index:pattern index"""
        j = ctypes.c_int()
        ierr = self._lib.EN_getpatternlen(self.ph, index, ctypes.byref(j))
        if ierr != 0:
            raise ENtoolkitError(self, ierr)
        return j.value

    def ENgetpatternvalue(self, index, period):
        """Retrieves the multiplier factor for a specific time period in a time pattern.

        Arguments:
        index:  time pattern index
        period: period within time pattern"""
        j = ctypes.c_float()
        ierr = self._lib.EN_getpatternvalue(self.ph, index, period, ctypes.byref(j))
        if ierr != 0:
            raise ENtoolkitError(self, ierr)
        return j.value

    def ENaddpattern(self, patid):
        """Adds a new time pattern to the network.

        ENaddpattern(patid)

        Arguments:
                patid: ID label of pattern

        OWA-EPANET Toolkit: http://wateranalytics.org/EPANET/group___patterns.html
        """

        ierr = self._lib.EN_addpattern(self.ph, ctypes.c_char_p(patid.encode(self.charset)))
        if ierr != 0:
            raise ENtoolkitError(self, ierr)

    def ENsetpattern(self, index, factors):
        """Sets all of the multiplier factors for a specific time pattern.
        Arguments:
        index:    time pattern index
        factors:  multiplier factors list for the entire pattern"""

        nfactors = len(factors)
        cfactors_type = ctypes.c_float * nfactors
        cfactors = cfactors_type()
        for i in range(nfactors):
            cfactors[i] = float(factors[i])
        ierr = self._lib.EN_setpattern(self.ph, ctypes.c_int(index), cfactors, ctypes.c_int(nfactors))
        if ierr != 0:
            raise ENtoolkitError(self, ierr)

    def ENsetpatternvalue(self, index, period, value):
        """Sets the multiplier factor for a specific period within a time pattern.
        Arguments:
           index: time pattern index
           period: period within time pattern
           value:  multiplier factor for the period"""
        # int ENsetpatternvalue( int index, int period, float value )
        ierr = self._lib.EN_setpatternvalue(self.ph, ctypes.c_int(index),
                                            ctypes.c_int(period),
                                            ctypes.c_float(value))
        if ierr != 0:
            raise ENtoolkitError(self, ierr)

    # Data Curve Functions

    def ENdeletecurve(self, index):
        """Deletes a data curve from a project.

        ARGUMENTS:
                index: the data curve's index (starting from 1).  """

        ierr = self._lib.EN_deletecurve(self.ph, ctypes.c_int(index))
        if ierr != 0:
            raise ENtoolkitError(self, ierr)

    def ENgetcurve(self, curveIndex):
        curveid = ctypes.create_string_buffer(self._max_label_len)
        nValues = ctypes.c_int()
        xValues = (ctypes.c_float * 100)()
        yValues = (ctypes.c_float * 100)()
        ierr = self._lib.EN_getcurve(self.ph, curveIndex,
                                     ctypes.byref(curveid),
                                     ctypes.byref(nValues),
                                     xValues,
                                     yValues
                                     )
        # strange behavior of ENgetcurve: it returns also curveID
        # better split in two distinct functions ....
        if ierr != 0:
            raise ENtoolkitError(self, ierr)
        curve = []
        for i in range(nValues.value):
            curve.append((xValues[i], yValues[i]))
        return curve

    def ENgetcurveid(self, curveIndex):
        curveid = ctypes.create_string_buffer(self._max_label_len)
        nValues = ctypes.c_int()

        xValues = (ctypes.c_float * 100)()
        yValues = (ctypes.c_float * 100)()

        ierr = self._lib.EN_getcurve(self.ph, curveIndex,
                                     ctypes.byref(curveid),
                                     ctypes.byref(nValues),
                                     xValues,
                                     yValues)
        # strange behavior of ENgetcurve: it returns also curveID
        # better split in two distinct functions ....
        if ierr != 0:
            raise ENtoolkitError(self, ierr)
        return curveid.value.decode(self.charset)

    def ENgetcurveindex(self, curveId):
        j = ctypes.c_int()
        ierr = self._lib.EN_getcurveindex(self.ph, ctypes.c_char_p(curveId.encode(self.charset)), ctypes.byref(j))
        if ierr != 0:
            raise ENtoolkitError(self, ierr)
        return j.value

    def ENgetcurvelen(self, curveIndex):
        j = ctypes.c_int()
        ierr = self._lib.EN_getcurvelen(self.ph, ctypes.c_int(curveIndex), ctypes.byref(j))
        if ierr != 0:
            raise ENtoolkitError(self, ierr)
        return j.value

    def ENgetcurvetype(self, curveIndex):
        """Arguments:
        curveIndex: Types of data curves
                    EN_VOLUME_CURVE  = 0
                    EN_PUMP_CURVE    = 1
                    EN_EFFIC_CURVE   = 2
                    EN_HLOSS_CURVE   = 3
                    EN_GENERIC_CURVE = 4  """

        j = ctypes.c_int()
        ierr = self._lib.EN_getcurvetype(self.ph, curveIndex, ctypes.byref(j))
        if ierr != 0:
            raise ENtoolkitError(self, ierr)
        return j.value

    def ENgetcurvevalue(self, curveIndex, point):
        x = ctypes.c_float()
        y = ctypes.c_float()
        ierr = self._lib.EN_getcurvevalue(self.ph, ctypes.c_int(curveIndex), ctypes.c_int(point - 1), ctypes.byref(x),
                                          ctypes.byref(y))
        if ierr != 0:
            raise ENtoolkitError(self, ierr)
        return x.value, y.value

    def ENsetcurve(self, curveIndex, values):

        """ Assigns a set of data points to a curve.

        net.ep.ENsetcurve(index,[[x,y],[x,y],[])
        """

        nValues = len(values)
        Values_type = ctypes.c_float * nValues
        xValues = Values_type()
        yValues = Values_type()
        for i in range(nValues):
            xValues[i] = float(values[i][0])
            yValues[i] = float(values[i][1])

        ierr = self._lib.EN_setcurve(self.ph, curveIndex, xValues, yValues, nValues)

        if ierr != 0:
            raise ENtoolkitError(self, ierr)

    def ENsetcurvetype(self, curve_index, curve_type):

        """Sets a curve's type.
         ARGUMENTS:
         curve_index	a curve's index (starting from 1).
         curve_type	the curve's type (see EN_CurveType). """

        ierr = self._lib.EN_setcurvetype(self.ph, ctypes.c_int(curve_index), ctypes.c_int(curve_type))

        if ierr != 0:
            raise ENtoolkitError(self, ierr)

    def ENsetcurvevalue(self, curve_index, point_index, x, y):
        """Sets the value of a single data point for a curve.

            ARGUMENTS:
                    curve_Index	a curve's index (starting from 1).
                    pointIndex	the index of a point on the curve (starting from 1).
                    x	the point's new x-value.
                    y	the point's new y-value.   """

        ierr = self._lib.EN_setcurvevalue(self.ph, ctypes.c_int(curve_index), ctypes.c_int(point_index),
                                          ctypes.c_float(x), ctypes.c_float(y))
        if ierr != 0:
            raise ENtoolkitError(self, ierr)

    def ENaddcurve(self, curve_id):
        """ Adds a new data curve to a project.


        ENaddcurve(cid)

        Parameters:
        curve_id        The ID name of the curve to be added.

        """
        ierr = self._lib.EN_addcurve(self.ph, ctypes.c_char_p(curve_id.encode(self.charset)))
        if ierr != 0:
            raise ENtoolkitError(self, ierr)

    # Simple Control Functions

    def ENaddcontrol(self, ctype, lindex, setting, nindex, level):
        """Sets the parameters of a simple control statement.
        Arguments:
           ctype:   control type code  EN_LOWLEVEL   (Low Level Control)
                                       EN_HILEVEL    (High Level Control)
                                       EN_TIMER      (Timer Control)
                                       EN_TIMEOFDAY  (Time-of-Day Control)
           lindex:  index of link being controlled
           setting: value of the control setting
           nindex:  index of controlling node
           level:   value of controlling water level or pressure for level controls
                    or of time of control action (in seconds) for time-based controls"""
        # int ENsetcontrol(int cindex, int* ctype, int* lindex, float* setting, int* nindex, float* level )
        cindex = ctypes.c_int()
        ierr = self._lib.EN_addcontrol(self.ph, ctypes.c_int(ctype),
                                       ctypes.c_int(lindex), ctypes.c_float(setting),
                                       ctypes.c_int(nindex), ctypes.c_double(level), ctypes.byref(cindex))
        if ierr != 0:
            raise ENtoolkitError(self, ierr)
        return cindex

    def ENdeletecontrol(self, index):
        """Deletes an existing simple control.

        ARGUMENTS:
                index: The index of the control to delete (starting from 1). """

        ierr = self._lib.EN_deletecontrol(self.ph, ctypes.c_int(index))
        if ierr != 0:
            raise ENtoolkitError(self, ierr)

    def ENgetcontrol(self, cindex):  # <------------
        """Retrieves the parameters of a simple control statement.
        Arguments:
           cindex:  control statement index

        returns: ctype:  control type code:
                        EN_LOWLEVEL   (Low Level Control)
                        EN_HILEVEL    (High Level Control)
                        EN_TIMER      (Timer Control)
                        EN_TIMEOFDAY  (Time-of-Day Control)
                lindex:  index of link being controlled
                setting: value of the control setting
                nindex:  index of controlling node
                level:   value of controlling water level or pressure for level controls
                            or of time of control action (in seconds) for time-based controls
        """
        type_ = ctypes.c_int()  # <--------------
        lindex = ctypes.c_int()  # <-------------
        setting = ctypes.c_float()  # <----------
        nindex = ctypes.c_int()  # <------------
        level = ctypes.c_float()  # <------------
        ierr = self._lib.EN_getcontrol(self.ph, ctypes.c_int(cindex), ctypes.byref(type_), ctypes.byref(lindex),
                                       ctypes.byref(setting), ctypes.byref(nindex), ctypes.byref(level),
                                       ctypes.byref(level))  # <------------
        if ierr != 0:
            raise ENtoolkitError(self, ierr)
        return type_.value, lindex.value, setting.value, nindex.value, level.value  # <------------

    def ENsetcontrol(self, cindex, ctype, lindex, setting, nindex, level):
        """Sets the parameters of a simple control statement.
           Arguments:
                    cindex  :   control statement index
                    ctype  :    control type code   EN_LOWLEVEL   (Low Level Control)
                                                    EN_HILEVEL    (High Level Control)
                                                    EN_TIMER      (Timer Control)
                                                    EN_TIMEOFDAY  (Time-of-Day Control)
                    lindex  :   index of link being controlled
                    setting :   value of the control setting
                    nindex  :   index of controlling node
                    level   :   value of controlling water level or pressure for level controls
                                or of time of control action (in seconds) for time-based controls
        """
        # int ENsetcontrol(int cindex, int* ctype, int* lindex, float* setting, int* nindex, float* level )
        ierr = self._lib.EN_setcontrol(self.ph, ctypes.c_int(cindex), ctypes.c_int(ctype),
                                       ctypes.c_int(lindex), ctypes.c_float(setting),
                                       ctypes.c_int(nindex), ctypes.c_float(level))
        if ierr != 0:
            raise ENtoolkitError(self, ierr)

    # Rule-Based Control Functions

    def ENaddrule(self, rule):
        """Adds a new rule-based control to a project.

         ENaddrule(rule)

        Arguments:
                rule: text of the rule following the format used in an EPANET input file.
                OWA-EPANET Toolkit: http://wateranalytics.org/EPANET/group___rules.html
        """

        ierr = self._lib.EN_addrule(self.ph, ctypes.c_char_p(rule.encode(self.charset)))
        if ierr != 0:
            raise ENtoolkitError(self, ierr)

    def ENdeleterule(self, index):
        """Deletes an existing rule-based control.
        Arguments:
                index: the index of the rule to be deleted (starting from 1) """

        ierr = self._lib.EN_deleterule(self.ph, ctypes.c_int(index))
        if ierr != 0:
            raise ENtoolkitError(self, ierr)

    def ENgetrule(self, index):
        """Retrieves the index of a particular rule.
        	Arguments:
        			index			:	the rule's index (starting from 1).
        	[out]	nPremises		:	number of premises in the rule's IF section.
        	[out]	nThenActions	:	number of actions in the rule's THEN section.
        	[out]	nElseActions	:	number of actions in the rule's ELSE section.
        	[out]	priority		:	the rule's priority value.
        	"""

        j1 = ctypes.c_int()
        j2 = ctypes.c_int()
        j3 = ctypes.c_int()
        j4 = ctypes.c_float()
        ierr = self._lib.EN_getrule(self.ph, index, ctypes.byref(j1), ctypes.byref(j2), ctypes.byref(j3),
                                    ctypes.byref(j4))
        if ierr != 0:
            raise ENtoolkitError(self, ierr)
        return j1.value, j2.value, j3.value, j4.value

    def ENgetruleid(self, index):
        """Retrieves the ID label of a node with a specified index.
        Arguments:
        index: the rule's index (starting from 1)
        [out] out_id: the rule's ID name."""

        label = ctypes.create_string_buffer(self._max_label_len)
        ierr = self._lib.EN_getruleID(self.ph, index, ctypes.byref(label))
        if ierr != 0:
            raise ENtoolkitError(self, ierr)
        return label.value.decode(self.charset)

    def ENgetpremise(self, index, permiseIndex):
        """Gets the properties of a premise in a rule-based control.
           Arguments:
                    index   :	the rule's index (starting from 1)
                    permiseIndex:	the position of the premise in the rule's list of premises (starting from 1).
            [out]	logop		:	the premise's logical operator ( IF = 1, AND = 2, OR = 3 ).
            [out]	object		:	the type of object the premise refers to (see EN_RuleObject).
            [out]	objIndex	:	the index of the object (e.g. the index of a tank).
            [out]	variable	:	the object's variable being compared (see EN_RuleVariable).
            [out]	relop		:	the premise's comparison operator (see EN_RuleOperator).
            [out]	status		:	the status that the object's status is compared to (see EN_RuleStatus).
            [out]	value		:	the value that the object's variable is compared to.
        """

        j1 = ctypes.c_int()
        j2 = ctypes.c_int()
        j3 = ctypes.c_int()
        j4 = ctypes.c_int()
        j5 = ctypes.c_int()
        j6 = ctypes.c_int()
        j7 = ctypes.c_double()
        ierr = self._lib.EN_getpremise(self.ph, index, permiseIndex, ctypes.byref(j1), ctypes.byref(j2),
                                       ctypes.byref(j3),
                                       ctypes.byref(j4), ctypes.byref(j5), ctypes.byref(j6), ctypes.byref(j7))
        if ierr != 0:
            raise ENtoolkitError(self, ierr)
        return j1.value, j2.value, j3.value, j4.value, j5.value, j6.value, j7.value

    def ENsetpremise(self, index, premiseIndex, logop, object, objindex, variable, relop, status, value):
        """Sets the properties of a premise in a rule-based control.

        Arguments:
            index	        the rule's index (starting from 1).
            premiseIndex	the position of the premise in the rule's list of premises.
            logop	        the premise's logical operator ( IF = 1, AND = 2, OR = 3 ).
            object	        the type of object the premise refers to (see EN_RuleObject).
            objIndex	    the index of the object (e.g. the index of a tank).
            variable	    the object's variable being compared (see EN_RuleVariable).
            relop	        the premise's comparison operator (see EN_RuleOperator).
            status	        the status that the object's status is compared to (see EN_RuleStatus).
            value	        the value that the object's variable is compared to. """

        ierr = self._lib.EN_setpremise(self.ph, ctypes.c_int(index), ctypes.c_int(premiseIndex),
                                       ctypes.c_int(logop), ctypes.c_int(object), ctypes.c_int(objindex),
                                       ctypes.c_int(variable), ctypes.c_int(relop), ctypes.c_int(status),
                                       ctypes.c_float(value))
        if ierr != 0:
            raise ENtoolkitError(self, ierr)

    def ENgetthenaction(self, index, actionIndex):
        """Retrieves the properties of a THEN action in a rule-based control.
        Arguments:
        index: the rule's index (starting from 1).
        actionIndex:the index of the THEN action to retrieve (starting from 1).

        [out] linkIndex: the index of the link in the action(starting from 1).
        [out] status: the status assigned to the link(see EN_RuleStatus)
        [out] setting: the value assigned to the link's setting."""

        j1 = ctypes.c_int()
        j2 = ctypes.c_int()
        j3 = ctypes.c_double()
        ierr = self._lib.EN_getthenaction(self.ph, index, actionIndex, ctypes.byref(j1), ctypes.byref(j2),
                                          ctypes.byref(j3))
        if ierr != 0:
            raise ENtoolkitError(self, ierr)
        return j1.value, j2.value, j3.value

    def ENgetelseaction(self, index, actionIndex):
        """Retrieves the properties of a ELSE action in a rule-based control.
        Arguments:
        index: the rule's index (starting from 1).
        actionIndex:the index of the ELSE action to retrieve (starting from 1).

        [out] linkIndex: the index of the link in the action(starting from 1).
        [out] status: the status assigned to the link(see EN_RuleStatus)
        [out] setting: the value assigned to the link's setting."""

        j1 = ctypes.c_int()
        j2 = ctypes.c_int()
        j3 = ctypes.c_double()
        ierr = self._lib.EN_getelseaction(self.ph, index, actionIndex, ctypes.byref(j1), ctypes.byref(j2),
                                          ctypes.byref(j3))
        if ierr != 0:
            raise ENtoolkitError(self, ierr)
        return j1.value, j2.value, j3.value

    def ENsetelseaction(self, index, actionIndex, linkindex, status, setting):
        """Sets the properties of an ELSE action in a rule-based control.

        Arguments:
            index	        the rule's index (starting from 1).
            actionIndex  	the index of the ELSE action being modified (starting from 1).
            linkindex	    the index of the link in the action (starting from 1).
            status	        the new status assigned to the link (see EN_RuleStatus) .
            setting	        the new value assigned to the link's setting. """

        ierr = self._lib.EN_setelseaction(self.ph, ctypes.c_int(index), ctypes.c_int(actionIndex),
                                          ctypes.c_int(linkindex), ctypes.c_int(status), ctypes.c_double(setting))
        if ierr != 0:
            raise ENtoolkitError(self, ierr)

    def ENsetpremiseindex(self, index, premiseIndex, objindex):
        """Sets the index of an object in a premise of a rule-based control.

        Arguments:
            index	        the rule's index (starting from 1).
            premiseIndex	the premise's index (starting from 1).
            objIndex	    the index of the object (e.g. the index of a tank)."""

        ierr = self._lib.EN_setpremiseindex(self.ph, ctypes.c_int(index), ctypes.c_int(premiseIndex),
                                            ctypes.c_int(objindex))
        if ierr != 0:
            raise ENtoolkitError(self, ierr)

    def ENsetpremisestatus(self, index, premiseIndex, status):
        """Sets the status being compared to in a premise of a rule-based control.

        Arguments:
            index	        the rule's index (starting from 1).
            premiseIndex	the premise's index (starting from 1).
            status  	    the status that the premise's object status is compared to (see EN_RuleStatus). """

        ierr = self._lib.EN_setpremisestatus(self.ph, ctypes.c_int(index), ctypes.c_int(premiseIndex),
                                             ctypes.c_int(status))
        if ierr != 0:
            raise ENtoolkitError(self, ierr)

    def ENsetpremisevalue(self, index, premiseIndex, value):
        """Sets the value in a premise of a rule-based control.

        Arguments:
            index	        the rule's index (starting from 1).
            premiseIndex	the premise's index (starting from 1).
            value  	        The value that the premise's variable is compared to. """

        ierr = self._lib.EN_setpremisevalue(self.ph, ctypes.c_int(index), ctypes.c_int(premiseIndex),
                                            ctypes.c_double(value))
        if ierr != 0:
            raise ENtoolkitError(self, ierr)

    def ENsetrulepriority(self, index, priority):
        """Sets the priority of a rule-based control.

        Arguments:
            index	        the rule's index (starting from 1).
            priority	    the priority value assigned to the rule."""

        ierr = self._lib.EN_setrulepriority(self.ph, ctypes.c_int(index), ctypes.c_double(priority))
        if ierr != 0:
            raise ENtoolkitError(self, ierr)

    def ENsetthenaction(self, index, actionIndex, linkindex, status, setting):
        """Sets the properties of a THEN action in a rule-based control.

        Arguments:
            index	        the rule's index (starting from 1).
            actionIndex  	the index of the THEN action being modified (starting from 1).
            linkindex	    the index of the link in the action (starting from 1).
            status	        the new status assigned to the link (see EN_RuleStatus) .
            setting	        the new value assigned to the link's setting. """

        ierr = self._lib.EN_setthenaction(self.ph, ctypes.c_int(index), ctypes.c_int(actionIndex),
                                          ctypes.c_int(linkindex), ctypes.c_int(status), ctypes.c_double(setting))
        if ierr != 0:
            raise ENtoolkitError(self, ierr)

    # miscellaneous

    def ENgetcomment(self, object_type, index):
        """Retrieves the comment of an object with a object type and index

        Arguments:
        object_type: object type
        index: object index
        """
        label = ctypes.create_string_buffer(1024)
        ierr = self._lib.EN_getcomment(self.ph, object_type, index, ctypes.byref(label))
        if ierr != 0:
            raise ENtoolkitError(self, ierr)
        return label.value.decode(self.charset)

    def ENsetcomment(self, object_type, index, comment):
        """Retrieves the comment of an object with a object type and index

        Arguments:
        object_type: object type
        index: object index
        """
        ierr = self._lib.EN_setcomment(self.ph, object_type, index, ctypes.c_char_p(comment.encode(self.charset)))
        if ierr != 0:
            raise ENtoolkitError(self, ierr)

    def ENsimtime(self):
        """retrieves the current simulation time t as datetime.timedelta instance"""
        return datetime.timedelta(seconds=self._current_simulation_time.value)


# Enumerated Types

EN_ELEVATION = 0  # /* Node parameters */
EN_BASEDEMAND = 1
EN_PATTERN = 2
EN_EMITTER = 3
EN_INITQUAL = 4
EN_SOURCEQUAL = 5
EN_SOURCEPAT = 6
EN_SOURCETYPE = 7
EN_TANKLEVEL = 8
EN_DEMAND = 9
EN_HEAD = 10
EN_PRESSURE = 11
EN_QUALITY = 12
EN_SOURCEMASS = 13
EN_INITVOLUME = 14
EN_MIXMODEL = 15
EN_MIXZONEVOL = 16

EN_TANKDIAM = 17
EN_MINVOLUME = 18
EN_VOLCURVE = 19
EN_MINLEVEL = 20
EN_MAXLEVEL = 21
EN_MIXFRACTION = 22
EN_TANK_KBULK = 23
EN_TANKVOLUME = 24
EN_MAXVOLUME = 25
EN_CANOVERFLOW = 26
EN_DEMANDDEFICIT = 27
EN_NODE_INCONTROL = 28
EN_EMITTERFLOW = 29

EN_DIAMETER = 0  # /* Link parameters */
EN_LENGTH = 1
EN_ROUGHNESS = 2
EN_MINORLOSS = 3
EN_INITSTATUS = 4
EN_INITSETTING = 5
EN_KBULK = 6
EN_KWALL = 7
EN_FLOW = 8
EN_VELOCITY = 9
EN_HEADLOSS = 10
EN_STATUS = 11
EN_SETTING = 12
EN_ENERGY = 13
EN_LINKQUAL = 14
EN_LINKPATTERN = 15
EN_PUMP_STATE = 16
EN_PUMP_EFFIC = 17
EN_PUMP_POWER = 18
EN_PUMP_HCURVE = 19
EN_PUMP_ECURVE = 20
EN_PUMP_ECOST = 21
EN_PUMP_EPAT = 22
EN_LINK_INCONTROL = 23
EN_GPV_CURVE = 24
EN_PCV_CURVE = 25

EN_DURATION = 0  # /* Time parameters */
EN_HYDSTEP = 1
EN_QUALSTEP = 2
EN_PATTERNSTEP = 3
EN_PATTERNSTART = 4
EN_REPORTSTEP = 5
EN_REPORTSTART = 6
EN_RULESTEP = 7
EN_STATISTIC = 8
EN_PERIODS = 9
EN_STARTTIME = 10
EN_HTIME = 11
EN_QTIME = 12
EN_HALTFLAG = 13
EN_NEXTEVENT = 14
EN_NEXTEVENTTANK = 15

EN_NODECOUNT = 0  # /* Component counts */
EN_TANKCOUNT = 1
EN_LINKCOUNT = 2
EN_PATCOUNT = 3
EN_CURVECOUNT = 4
EN_CONTROLCOUNT = 5
EN_RULECOUNT = 6

EN_JUNCTION = 0  # /* Node types */
EN_RESERVOIR = 1
EN_TANK = 2

EN_CVPIPE = 0  # /* Link types */
EN_PIPE = 1
EN_PUMP = 2
EN_PRV = 3
EN_PSV = 4
EN_PBV = 5
EN_FCV = 6
EN_TCV = 7
EN_GPV = 8
EN_PCV = 9

EN_NONE = 0  # /* Quality analysis types */
EN_CHEM = 1
EN_AGE = 2
EN_TRACE = 3

EN_CONCEN = 0  # /* Source quality types */
EN_MASS = 1
EN_SETPOINT = 2
EN_FLOWPACED = 3

EN_CFS = 0  # /* Flow units types */
EN_GPM = 1
EN_MGD = 2
EN_IMGD = 3
EN_AFD = 4
EN_LPS = 5
EN_LPM = 6
EN_MLD = 7
EN_CMH = 8
EN_CMD = 9
EN_CMS = 10

EN_HW = 0  # /* Headloss type */
EN_DW = 1
EN_CM = 2

EN_TRIALS = 0  # /* Misc. options */
EN_ACCURACY = 1
EN_TOLERANCE = 2
EN_EMITEXPON = 3
EN_DEMANDMULT = 4
EN_HEADERROR = 5
EN_FLOWCHANGE = 6
EN_HEADLOSSFORM = 7
EN_GLOBALEFFIC = 8
EN_GLOBALPRICE = 9
EN_GLOBALPATTERN = 10
EN_DEMANDCHARGE = 11
EN_SP_GRAVITY = 12
EN_SP_VISCOS = 13
EN_UNBALANCED = 14
EN_CHECKFREQ = 15
EN_MAXCHECK = 16
EN_DAMPLIMIT = 17
EN_SP_DIFFUS = 18
EN_BULKORDER = 19
EN_WALLORDER = 20
EN_TANKORDER = 21
EN_CONCENLIMIT = 22
EN_DEMANDPATTERN = 23
EN_EMITBACKFLOW = 24
EN_PRESS_UNITS = 25
EN_STATUS_REPORT = 26

EN_LOWLEVEL = 0  # /* Control types */
EN_HILEVEL = 1
EN_TIMER = 2
EN_TIMEOFDAY = 3

EN_SERIES = 0  # /* Time statistic types.    */
EN_AVERAGE = 1
EN_MINIMUM = 2
EN_MAXIMUM = 3
EN_RANGE = 4

EN_MIX1 = 0  # /* Tank mixing models */
EN_MIX2 = 1
EN_FIFO = 2
EN_LIFO = 3

EN_NOSAVE = 0  # /* Save-results-to-file flag */
EN_SAVE = 1
EN_INITFLOW =10
EN_SAVE_AND_INIT = 4

EN_DDA = 0      # /* Demand model types   */
EN_PDA = 1

FlowUnits = {EN_CFS: "cf/s",
             EN_GPM: "gpm",
             EN_MGD: "Mg/d",
             EN_IMGD: "IMg/d",
             EN_AFD: "af/d",
             EN_LPS: "L/s",
             EN_LPM: "Lpm",
             EN_MLD: "ML/D",
             EN_CMH: "m3/h",
             EN_CMD: "m3/d",
             EN_CMS: "m3/s"}

EN_R_NODE = 0  # / *Network objects used in rule-based controls. */
EN_R_LINK = 1
EN_R_SYSTEM = 2

EN_R_EQ = 0  # / *Comparison operators used in rule-based controls. */
EN_R_NE = 1
EN_R_LE = 2
EN_R_GE = 3
EN_R_LT = 4
EN_R_GT = 5
EN_R_IS = 6
EN_R_NOT = 7
EN_R_BELOW = 8
EN_R_ABOVE = 9

N_R_IS_OPEN = 0  # / *Link status codes used in rule-based controls. */
EN_R_IS_CLOSED = 1
EN_R_IS_ACTIVE = 2

EN_R_DEMAND = 0  # / *Object variables used in rule-based controls. */
EN_R_HEAD = 1
EN_R_GRADE = 2
EN_R_LEVEL = 3
EN_R_PRESSURE = 4
EN_R_FLOW = 5
EN_R_STATUS = 6
EN_R_SETTING = 7
EN_R_POWER = 8
EN_R_TIME = 9
EN_R_CLOCKTIME = 10
EN_R_FILLTIME = 11
EN_R_DRAINTIME = 12

EN_VOLUME_CURVE = 0  # / *Types of data curves */
EN_PUMP_CURVE = 1
EN_EFFIC_CURVE = 2
EN_HLOSS_CURVE = 3
EN_GENERIC_CURVE = 4
EN_VALVE_CURVE = 5

EN_PSI = 0  # / *Pressure units. */
EN_KPA = 1
EN_METERS = 2


class ENtoolkitError(Exception):
    def __init__(self, epanet2: object, ierr: object) -> object:
        self.warning = ierr < 100
        self.args = (ierr,)
        self.message = epanet2.ENgeterror(ierr)

        if self.message == '' and ierr != 0:
            self.message = 'ENtoolkit Undocumented Error ' + str(ierr) + ': look at text.h in epanet sources'

    def __str__(self):
        return self.message
