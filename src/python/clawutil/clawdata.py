r"""
Data Module

Contains the general class definition and the subclasses of the Clawpack data
objects.

Changes in 5.0:
 Stripped down version of Data object, no longer keeps track of "owners".
 Data classes are now subclasses of ClawData, which checks if attributes
   already exist before setting.

"""

import os
import string

import numpy as np

# ==============================================================================
#  Base data class for Clawpack data objects
class ClawData(object):
    r"""
    Class to be subclassed when defining data objects that should have
    a limited set of allowed attributes.  Useful to guard against
    typos or misrembering the names of expected attributes.

    Resetting values of existing attributes is allowed as usual,
    but new attributes can only be added using the method add_attribute.

    Trying to set a nonexistent attribute will raise an AttributeError
    exception, except for those starting with '_'.   
    """


    def __init__(self, attributes=None):
        
        # Attribute to store a list of the allowed attributes, 
        # appended to when add_attribute is used: 
        object.__setattr__(self,'_attributes',[])

        # Output file handle
        object.__setattr__(self,'_out_file',None)

        # Initialize from attribute list provided
        if attributes:
            for attr in attributes:
                self.add_attribute(attr,None)


    def __setattr__(self,name,value):
        r"""
        Check that attribute exists before setting it.
        If not, raise an AttributeError.
        Exception: attributes starting with '_' are ok to set.
        """

        if (not name in self._attributes) and (name[0] != '_'):
            print "*** Unrecognized attribute: ",name
            print "*** Perhaps a typo?"
            print "*** Add new attributes using add_attribute method"
            raise AttributeError("Unrecognized attribute: %s" % name)
        
        # attribute exists, ok to set:
        object.__setattr__(self,name,value)


    def __str__(self):
        r"""Returns string representation of this object"""
        output = "%s%s\n" % ("Name".ljust(25),"Value".ljust(12))
        for (k,v) in self.iteritems():
            output += "%s%s\n" % (str(k).ljust(25),str(v).ljust(12))
        return output


    def add_attribute(self, name, value=None, add_to_list=True):
        r"""
        Adds an attribute called name to the data object

        If an attribute needs to be added to the object, this routine must be
        called or the attribute will not be written out.

        :Input:
         - *name* - (string) Name of the data attribute
         - *value* - (id) Value to set *name* to, defaults to None
        """
        if (name not in self._attributes) and add_to_list:
            self._attributes.append(name)
        object.__setattr__(self,name,value)


    def add_attributes(self, arg_list, value=None):
        r"""
        Add a list of attributes, each initialized to *value*.
        """
        for name in arg_list:
            self.add_attribute(name, value)


    def remove_attributes(self, arg_list):
        r"""
        Remove the listed attributes.
        """

        # Convert to list if args is not already a list
        if not isinstance(arg_list,list):
            arg_list = [arg_list]

        for arg in arg_list:
            self._attributes.remove(arg)
            delattr(self,arg)


    def attributes(self):
        r"""Returns tuple of attribute names"""
        return tuple(self._attributes)


    def has_attribute(self,name):
        r"""
        Check if this data object has the given attributes

        :Input:
         - *name* - (string) Name of attribute

        :Output:
         - (bool) - True if data object contains a data attribute name
        """
        return name in self._attributes

        
    def iteritems(self):
        r"""
        Returns an iterator of attributes and values from this object

        :Output:
         - (Iterator) Iterator over attributes and values
        """
        return [(k,getattr(self,k)) for k in self._attributes]


    def open_data_file(self, name, datasource='setrun.py'):
        """
        Open a data file and write a warning header.
        Warning header starts with '#' character.  These lines are skipped if
        data file is opened using the library routine opendatafile.

        :Input:
         - *name* - (string) Name of data file
         - *datasource* - (string) Source for the data

        :Output:
         - (file) - file object
        """

        source = string.ljust(datasource,25)
        self._out_file = open(name, 'w')
        self._out_file.write('########################################################\n')
        self._out_file.write('### DO NOT EDIT THIS FILE:  GENERATED AUTOMATICALLY ####\n')
        self._out_file.write('### To modify data, edit  %s ####\n' % source)
        self._out_file.write('###    and then "make .data"                        ####\n')
        self._out_file.write('########################################################\n\n')


    def close_data_file(self):
        r""""""
        self._out_file.close()
        self._out_file = None


    def write(self,out_file,data_source='setrun.py'):
        r""""""

        # Open data file
        self.open_data_file(out_file,data_source)

        # Write out list of attributes
        for (name,value) in self.iteritems():
            self.data_write(name)


    def data_write(self, name=None, value=None, alt_name=None, description=''):
        r"""
        Write out value to data file, in the form ::

           value =: name   # [description]

        Remove brackets and commas from lists, and replace booleans by T/F.

        :Input:
         - *name* - (string) normally a string defining the variable,
           ``if name==None``, write a blank line.
         - *description* - (string) optional description
        """
        if self._out_file is None:
            raise Exception("No file currently open for output.")

        # Defaults to the name of the variable requested
        if alt_name is None:
            alt_name = name

        if name is None and value is None:
            # Write out a blank line
            self._out_file.write('\n')
        else:
            # Use the value passed in instead of fetching from the data object
            if value is None:
                value = self.__getattribute__(name)

            # Convert value to an appropriate string repr
            if isinstance(value,np.ndarray):
                value = list(value)
            if isinstance(value,tuple) | isinstance(value,list):
                # Remove [], (), and ','
                string_value = repr(value)[1:-1]
                string_value = string_value.replace(',','')
            elif isinstance(value,bool):
                if value:
                    string_value = 'T'
                else:
                    string_value = 'F'
            else:
                string_value = repr(value)
            padded_value = string.ljust(string_value, 20)
            padded_name = string.ljust(alt_name,20)
            if description != '':
                self._out_file.write('%s =: %s # %s \n' % 
                                        (padded_value, padded_name, description))
            else:
                self._out_file.write('%s =: %s\n' % 
                                    (padded_value, padded_name))
  

    def read(self,path,force=False):
        r"""Read and fill applicable data attributes.

        Note that if the data attribute is not found an exception will be
        raised unless the force argument is set to True in which case a new
        attribute will be added.
        """

        data_file = open(os.path.abspath(path),'r')

        for lineno,line in enumerate(data_file):
            if "=:" not in line:
                continue

            value, tail = line.split("=:")
            varname = tail.split()[0]

            # Set this parameter
            if self.has_attribute(varname) or force:
                value = self._parse_value(value)
                if not self.has_attribute(varname):
                    self.add_attribute(varname,value)
                else:
                    setattr(self,varname,value)
    

    def _parse_value(self,value):
        r"""
        Attempt to make sense of a value string from a config file.  If the
        value is not obviously an integer, float, or boolean, it is returned as
        a string stripped of leading and trailing whitespace.

        :Input:
            - *value* - (string) Value string to be parsed

        :Output:
            - (id) - Appropriate object based on *value*
        """
        value = value.strip()
        if not value:
            return None

        # assume that values containing spaces are lists of values
        if len(value.split()) > 1:
            return [self._parse_value(vv) for vv in value.split()]

        try:
            # see if it's an integer
            value = int(value)
        except ValueError:
            try:
                # see if it's a float
                value = float(value)
            except ValueError:
                # see if it's a bool
                if value[0] == 'T':
                    value = True
                elif value[0] == 'F':
                    value = False

        return value

#  Base data class for Clawpack data objects
# ==============================================================================


# ==============================================================================
# Clawpack input data classes
class ClawRunData(ClawData):
    r"""
    Object that contains all data objects that need to written out.

    Depending on the package type, this object contains the necessary data
    objects that need to eventually be written out to files.
    """

    def __init__(self, pkg, num_dim):
        super(ClawRunData,self).__init__()
        self.add_attribute('pkg',pkg)
        self.add_attribute('num_dim',num_dim)
        self.add_attribute('data_list',[])
        self.add_attribute('xclawcmd',None)


        # Add package specific data objects
        if pkg.lower() in ['classic', 'classicclaw']:
            self.xclawcmd = 'xclaw'

            self.add_data(ClawInputData(num_dim),'clawdata')

        elif pkg.lower() in ['amrclaw', 'amr']:
            self.xclawcmd = 'xamr'

            self.add_data(AmrclawInputData(num_dim),'clawdata')
            self.add_data(RegionData(),'regiondata')
            self.add_data(GaugeData(),'gaugedata')

        elif pkg.lower() in ['geoclaw']:
            self.xclawcmd = 'xgeoclaw'

            # Required data set for basic run parameters:
            self.add_data(AmrclawInputData(num_dim),'clawdata')
            self.add_data(GeoclawInputData(num_dim),'geodata')
            self.add_data(RegionData(),'regiondata')
            self.add_data(GaugeData(),'gaugedata')
            self.add_data(QinitData(),'qinitdata')

        else:
            raise AttributeError("Unrecognized Clawpack pkg = %s" % pkg)


    def add_data(self,data,name,file_name=None):
        r"""Add data object named *name* and written to *file_name*."""
        self.add_attribute(name,data)
        self.data_list.append(data)


    def new_UserData(self,name,fname):
        r"""
        Create a new attribute called name
        for application specific data to be written
        to the data file fname.
        """
        data = UserData(fname)
        self.add_data(data,name,fname)
        return data


    def write(self):
        r"""Write out each data objects in datalist """
        for data_object in self.data_list:
            data_object.write()



class ClawInputData(ClawData):
    r"""
    Object containing basic Clawpack input data, usually written to 'claw.data'.


    """

    def __init__(self, num_dim):
        super(ClawInputData,self).__init__()

        # Set default values:
        self.add_attribute('num_dim',num_dim)
        self.add_attribute('num_eqn',1)
        self.add_attribute('num_waves',1)
        self.add_attribute('num_aux',0)
        self.add_attribute('output_style',1)
        self.add_attribute('output_times',[])
        self.add_attribute('num_output_times',None)
        self.add_attribute('output_t0',True)
        self.add_attribute('output_step_interval',None)
        self.add_attribute('total_steps',None)
        self.add_attribute('tfinal',None)
        self.add_attribute('output_format',1)
        self.add_attribute('output_q_components','all')
        self.add_attribute('output_aux_components',[])
        self.add_attribute('output_aux_onlyonce',True)
        
        self.add_attribute('dt_initial',1.e-5)
        self.add_attribute('dt_max',1.e99)
        self.add_attribute('dt_variable',1)
        self.add_attribute('cfl_desired',0.9)
        self.add_attribute('cfl_max',1.0)
        self.add_attribute('steps_max',50000)
        self.add_attribute('order',2)
        self.add_attribute('transverse_waves',2)
        self.add_attribute('dimensional_split',0)
        self.add_attribute('verbosity',0)
        self.add_attribute('verbosity_regrid',0)
        self.add_attribute('source_split',0)
        self.add_attribute('capa_index',0)
        self.add_attribute('limiter',[4])
        self.add_attribute('t0',0.)
        self.add_attribute('num_ghost',2)
        self.add_attribute('use_fwaves',False)
        self.add_attribute('restart',False)
        self.add_attribute('restart_file','')

        if num_dim == 1:
            self.add_attribute('lower',[0.])
            self.add_attribute('upper',[1.])
            self.add_attribute('num_cells',[100])
            self.add_attribute('bc_lower',[0])
            self.add_attribute('bc_upper',[0])
        elif num_dim == 2:
            self.add_attribute('lower',[0.,0.])
            self.add_attribute('upper',[1.,1.])
            self.add_attribute('num_cells',[100,100])
            self.add_attribute('bc_lower',[0,0])
            self.add_attribute('bc_upper',[0,0])
        elif num_dim == 3:
            self.add_attribute('lower',[0.,0.,0.])
            self.add_attribute('upper',[1.,1.,1.])
            self.add_attribute('num_cells',[100,100,100])
            self.add_attribute('bc_lower',[0,0,0])
            self.add_attribute('bc_upper',[0,0,0])
        else:
            raise ValueError("Only num_dim=1, 2, or 3 supported ")


    def write(self, out_file='claw.data', data_source='setrun.py'):
        r""""""
        self.open_data_file(out_file,data_source)

        self.data_write('num_dim')
        self.data_write('lower')
        self.data_write('upper')
        self.data_write('num_cells')
        self.data_write()  # writes blank line
        self.data_write('num_eqn')
        self.data_write('num_waves')
        self.data_write('num_aux')
        self.data_write()  # writes blank line

        self.data_write('t0')
        self.data_write()
        self.data_write('output_style')

        if self.output_style == 1:
            self.data_write('num_output_times')
            self.data_write('tfinal')
            self.data_write('output_t0')
        elif self.output_style == 2:
            if len(self.output_times) == 0:
                raise AttributeError("*** output_style==2 requires nonempty list" \
                        + " of output times")
            self.num_output_times = len(self.output_times)
            self.data_write('num_output_times')
            self.data_write('output_times')
        elif self.output_style==3:
            self.data_write('output_step_interval')
            self.data_write('total_steps')
            self.data_write('output_t0')
        else:
            raise AttributeError("*** Unrecognized output_style: %s"\
                  % self.output_style)
            

        self.data_write()
        if self.output_format in [1,'ascii']:
            self.output_format = 1
        elif self.output_format in [2,'netcdf']:
            self.output_format = 2
        elif self.output_format in [3,'binary']:
            self.output_format = 3
        else:
            raise ValueError("*** Error in data parameter: " + \
                  "output_format unrecognized: ",clawdata.output_format)
            
        self.data_write('output_format')

        if self.output_q_components == 'all':
            iout_q = self.num_eqn * [1]
        elif self.output_q_components == 'none':
            iout_q = self.num_eqn * [0]
        else:
            iout_q = np.where(self.output_q_components, 1, 0)

        # Write out local value of iout_q rather than a data member
        self.data_write('', value=iout_q, alt_name='iout_q')

        if self.num_aux > 0:
            if self.output_aux_components == 'all':
                iout_aux = self.num_aux * [1]
            elif self.output_aux_components == 'none':
                iout_aux = self.num_aux * [0]
            else:
                iout_aux = np.where(self.output_aux_components, 1, 0)
            self.data_write(name='', value=iout_aux, alt_name='iout_aux')
            self.data_write('output_aux_onlyonce')

        self.data_write()
        self.data_write('dt_initial')
        self.data_write('dt_max')
        self.data_write('cfl_max')
        self.data_write('cfl_desired')
        self.data_write('steps_max')
        self.data_write()
        self.data_write('dt_variable')
        self.data_write('order')

        if self.num_dim == 1:
            pass
        else:
            if self.transverse_waves in [0,'none']:  
                self.transverse_waves = 0
            elif self.transverse_waves in [1,'increment']:  
                self.transverse_waves = 1
            elif self.transverse_waves in [2,'all']:  
                self.transverse_waves = 2
            else:
                raise AttributeError("Unrecognized transverse_waves: %s" \
                      % self.transverse_waves)
            self.data_write(file, self.transverse_waves, 'transverse_waves')

            if self.dimensional_split in [0,'unsplit']:  
                self.dimensional_split = 0
            elif self.dimensional_split in [1,'godunov']:  
                self.dimensional_split = 1
            elif self.dimensional_split in [2,'strang']:  
                self.dimensional_split = 2
            else:
                raise AttributeError("Unrecognized dimensional_split: %s" \
                      % self.dimensional_split)
            self.data_write('dimensional_split')
            
        self.data_write('verbosity')

        if self.source_split in [0,'none']:  
            self.source_split = 0
        elif self.source_split in [1,'godunov']:  
            self.source_split = 1
        elif self.source_split in [2,'strang']:  
            self.source_split = 2
        else:
            raise AttributeError("Unrecognized source_split: %s" \
                  % self.source_split)
        self.data_write('source_split')

        self.data_write('capa_index')
        if self.num_aux > 0:
            self.data_write(file, self.aux_type, 'aux_type')
        self.data_write('use_fwaves')
        self.data_write()

        for i in range(len(self.limiter)):
            if self.limiter[i] in [0,'none']:        self.limiter[i] = 0
            elif self.limiter[i] in [1,'minmod']:    self.limiter[i] = 1
            elif self.limiter[i] in [2,'superbee']:  self.limiter[i] = 2
            elif self.limiter[i] in [3,'mc']:        self.limiter[i] = 3
            elif self.limiter[i] in [4,'vanleer']:   self.limiter[i] = 4
            else:
                raise AttributeError("Unrecognized limiter: %s" \
                      % self.limiter[i])
        self.data_write('limiter')

        self.data_write()

        self.data_write('num_ghost')
        for i in range(self.num_dim):
            if self.bc_lower[i] in [0,'user']:       self.bc_lower[i] = 0
            elif self.bc_lower[i] in [1,'extrap']:   self.bc_lower[i] = 1
            elif self.bc_lower[i] in [2,'periodic']: self.bc_lower[i] = 2
            elif self.bc_lower[i] in [3,'wall']:     self.bc_lower[i] = 3
            else:
                raise AttributeError("Unrecognized bc_lower: %s" \
                      % self.bc_lower[i])
        self.data_write('bc_lower')

        for i in range(self.num_dim):
            if self.bc_upper[i] in [0,'user']:       self.bc_upper[i] = 0
            elif self.bc_upper[i] in [1,'extrap']:   self.bc_upper[i] = 1
            elif self.bc_upper[i] in [2,'periodic']: self.bc_upper[i] = 2
            elif self.bc_upper[i] in [3,'wall']:     self.bc_upper[i] = 3
            else:
                raise AttributeError("Unrecognized bc_upper: %s" \
                      % self.bc_upper[i])
        self.data_write('bc_upper')

        self.data_write()
        self.data_write('restart')
        self.data_write('restart_file')
        self.data_write('checkpt_style')
        if self.checkpt_style==2:
            num_checkpt_times = len(self.checkpt_times)
            self.data_write(name='', value=num_checkpt_times, alt_name='num_checkpt_times')
            self.data_write('checkpt_times')
        elif self.checkpt_style==3:
            self.data_write('checkpt_interval')
        elif self.checkpt_style not in [0,1]:
            raise AttributeError("*** Unrecognized checkpt_style: %s"\
                  % self.checkpt_style)

        self.data_write()



class AmrclawInputData(ClawInputData):
    r"""
    Data object containing AMRClaw input data.

    Extends ClawInputData adding necessary data for AMR.
    """
    def __init__(self, num_dim):

        # Some defaults are inherited from ClawInputData:
        super(AmrclawInputData,self).__init__(num_dim)
        
        self.add_attribute('amr_levels_max',1)
        self.add_attribute('refinement_ratios_x',[1])
        self.add_attribute('refinement_ratios_y',[1])
        if num_dim == 3:
            self.add_attribute('refinement_ratios_z',[1])
        if num_dim == 1:
            raise NotImplemented("1d AMR not yet supported")
        self.add_attribute('variable_dt_refinement_ratios',False)

        self.add_attribute('refinement_ratios_t',[1])
        self.add_attribute('aux_type',[])

        self.add_attribute('checkpt_style',1)
        self.add_attribute('checkpt_interval',1000)
        self.add_attribute('checkpt_time_interval',1000.)
        self.add_attribute('checkpt_times',[1000.])
        
        self.add_attribute('flag_richardson',False)
        self.add_attribute('flag_richardson_tol',1.0)
        self.add_attribute('flag2refine',True)
        self.add_attribute('flag2refine_tol',0.05)
        self.add_attribute('regrid_interval',2)
        self.add_attribute('regrid_buffer_width',3)
        self.add_attribute('clustering_cutoff',0.7)

        
        # debugging flags:
        self.add_attribute('dprint',False)
        self.add_attribute('eprint',False)
        self.add_attribute('edebug',False)
        self.add_attribute('gprint',False)
        self.add_attribute('nprint',False)
        self.add_attribute('pprint',False)
        self.add_attribute('rprint',False)
        self.add_attribute('sprint',False)
        self.add_attribute('tprint',False)
        self.add_attribute('uprint',False)


    def write(self, out_file='amrclaw.data', data_source='setrun.py'):

        super(AmrclawInputData,self).write(out_file, data_source)
    
        self.data_write('amr_levels_max')

        num_ratios = max(abs(self.amr_levels_max)-1, 1)
        if len(self.refinement_ratios_x) < num_ratios:
            raise ValueError("*** Error in data parameter: " + \
                  "require len(refinement_ratios_x) >= %s " % num_ratios)
        if len(self.refinement_ratios_y) < num_ratios:
            raise ValueError("*** Error in data parameter: " + \
                  "require len(refinement_ratios_y) >= %s " % num_ratios)
        self.data_write('refinement_ratios_x')
        self.data_write('refinement_ratios_y')
        if self.num_dim == 3:
            if len(self.refinement_ratios_z) < num_ratios:
                    raise ValueError("*** Error in data parameter: " + \
                      "require len(refinement_ratios_z) >= %s " % num_ratios)
            self.data_write('refinement_ratios_z')
        if len(self.refinement_ratios_t) < num_ratios:
            raise ValueError("*** Error in data parameter: " + \
                  "require len(refinement_ratios_t) >= %s " % num_ratios)
        self.data_write('refinement_ratios_t')

        self.data_write()  # writes blank line

        self.data_write('flag_richardson')
        self.data_write('flag_richardson_tol')
        self.data_write('flag2refine')
        self.data_write('flag2refine_tol')
        self.data_write('regrid_interval')
        self.data_write('regrid_buffer_width')
        self.data_write('clustering_cutoff')
        self.data_write('verbosity_regrid')
        self.data_write()

        self.data_write()

        self.data_write('dprint')
        self.data_write('eprint')
        self.data_write('edebug')
        self.data_write('gprint')
        self.data_write('nprint')
        self.data_write('pprint')
        self.data_write('rprint')
        self.data_write('sprint')
        self.data_write('tprint')
        self.data_write('uprint')
        self.data_write()



class GeoclawInputData(ClawData):
    r"""
    Object that will be written out to the various GeoClaw data files.

    Note that this data object will write out multiple files.
    """
    def __init__(self, num_dim):
        super(GeoclawInputData,self).__init__()

        # GeoClaw physics parameters
        self.add_attribute('gravity',9.8)
        self.add_attribute('earth_radius',6367500.0)
        self.add_attribute('coordinate_system',1)
        self.add_attribute('coriolis_forcing',True)
        self.add_attribute('theta_0',45.0)
        self.add_attribute('friction_forcing',True)
        self.add_attribute('manning_coefficient',0.025)

        # GeoClaw algorithm parameters
        self.add_attribute('friction_depth',1.0e6)
        self.add_attribute('sea_level',0.0)
        self.add_attribute('variable_dt_refinement_ratios',False)

        # Refinement controls
        self.add_attribute('dry_tolerance',1.0e-3)
        self.add_attribute('wave_tolerance',1.0e-1)
        self.add_attribute('speed_tolerance',[1.0e12]*6)
        self.add_attribute('deep_depth',1.0e2)
        self.add_attribute('max_level_deep',3)
        
        # Topography data
        self.add_attribute('test_topography',0)
        self.add_attribute('topofiles',[])
        
        self.add_attribute('topo_location',-50e3)
        self.add_attribute('topo_left',-4000.0)
        self.add_attribute('topo_right',-200.0)
        self.add_attribute('topo_angle',0.0)
        
        self.add_attribute('x0',350e3)
        self.add_attribute('x1',450e3)
        self.add_attribute('x2',480e3)
        self.add_attribute('basin_depth',-3000.0)
        self.add_attribute('shelf_depth',-100.0)
        self.add_attribute('beach_slope',0.008)
        
        # Moving topograhpy
        self.add_attribute('dtopofiles',[])
        
        # Fixed Grids
        self.add_attribute('fixedgrids',[])


    def write(self,data_source='setrun.py'):

        self.open_data_file('geoclaw.data',data_source)

        self.data_write('gravity')
        self.data_write('earth_radius')
        self.data_write('coordinate_system')
        self.data_write('sea_level')
        self.data_write()

        # Forcing terms
        self.data_write('coriolis_forcing')
        if self.coordinate_system == 1 and self.coriolis_forcing:
            self.data_write('theta_0')
        self.data_write('friction_forcing')
        if self.friction_forcing:
            self.data_write('manning_coefficient')
            self.data_write('friction_depth')
        self.data_write()
        
        self.data_write('dry_tolerance')
        self.data_write('variable_dt_refinement_ratios')

        self.close_data_file()
        
        # Refinement controls
        self.open_data_file('refinement.data',data_source)
        self.data_write('wave_tolerance')
        if not isinstance(self.speed_tolerance,list):
            self.speed_tolerance = [self.speed_tolerance]
        self.data_write('speed_tolerance')
        self.data_write('deep_depth')
        self.data_write('max_level_deep')
        self.data_write()

        # Topography data
        self.open_data_file('topo.data',data_source)
        self.data_write(name='test_topography',description='(Type topography specification)')
        if self.test_topography == 0:
            ntopofiles = len(self.topofiles)
            self.data_write(value=ntopofiles,alt_name='ntopofiles')
            for tfile in self.topofiles:
                try:
                    fname = os.path.abspath(tfile[-1])
                except:
                    print "*** Error: file not found: ",tfile[-1]
                    raise ("file not found")
                self._out_file.write("\n'%s' \n " % fname)
                self._out_file.write("%3i %3i %3i %20.10e %20.10e \n" % tuple(tfile[:-1]))
        elif self.test_topography == 1:
            self.data_write(name='topo_location',description='(Bathymetry jump location)')
            self.data_write(name='topo_left',description='(Depth to left of bathy_location)')
            self.data_write(name='topo_right',description='(Depth to right of bathy_location)')
        elif self.test_topography == 2 or self.test_topography == 3: 
            self.data_write(name='x0',description='(Location of basin end)')
            self.data_write(name='x1',description='(Location of shelf slope end)')
            self.data_write(name='x2',description='(Location of beach slope)')
            self.data_write(name='basin_depth',description='(Depth of basin)')
            self.data_write(name='shelf_depth',description='(Depth of shelf)')
            self.data_write(name='beach_slope',description='(Slope of beach)')
        else:
            raise NotImplementedError("Test topography type %s has not been"
                                        " implemented." % self.test_topography)    
        self.close_data_file()

        # Moving topography settings
        self.open_data_file('dtopo.data',data_source)
        mdtopofiles = len(self.dtopofiles)
        self.data_write(value=mdtopofiles,alt_name='mdtopofiles')
        self.data_write()
        for tfile in self.dtopofiles:
            try:
                fname = "'%s'" % os.path.abspath(tfile[-1])
            except:
                # print "*** Error: file not found: ",tfile[-1]
                raise IOError("file not found")
            self._out_file.write("\n%s \n" % fname)
            self._out_file.write("%3i %3i %3i\n" % tuple(tfile[:-1]))
        self.close_data_file()

        # Fixed grid settings
        self.open_data_file('fixed_grids.data',data_source)
        nfixedgrids = len(self.fixedgrids)
        self.data_write(value=nfixedgrids,alt_name='nfixedgrids')
        self.data_write()
        for fixedgrid in self.fixedgrids:
            self._out_file.write(11*"%g  " % tuple(fixedgrid) +"\n")
        self.close_data_file()


class QinitData(ClawData):

    def __init__(self):

        super(QinitData,self).__init__()
        
        # Qinit data
        self.add_attribute('qinit_type',0)
        self.add_attribute('qinitfiles',[])    

    def write(self,data_source='setrun.py'):
        # Initial perturbation
        self.open_data_file('qinit.data',data_source)
        self.data_write('qinit_type')

        # Perturbation requested
        self.data_write()
        # Check to see if each qinit file is present and then write the data
        for tfile in self.qinitfiles:
            try:
                fname = "'%s'" % os.path.abspath(tfile[-1])
            except:
                raise MissingFile("file not found")
            self._out_file.write("\n%s  \n" % fname)
            self._out_file.write("%3i %3i \n" % tuple(tfile[:-1]))
        self.close_data_file()


# Clawpack input data classes
# ==============================================================================

# ==============================================================================
#  Region data object
class RegionData(ClawData):
    r""""""

    def __init__(self,regions=None):

        super(RegionData,self).__init__()

        if regions is None or not isinstance(regions,list):
            self.add_attribute('regions',[])
        else:
            self.add_attribute('regions',regions)


    def write(self,out_file='regions.data',data_source='setrun.py'):

        self.open_data_file(out_file,data_source)

        self.data_write(value=len(self.regions),alt_name='num_regions')
        for regions in self.regions:
            self._out_file.write(8*"%g  " % tuple(regions) +"\n")
        self.close_data_file()

# ==============================================================================
        
# ==============================================================================
#  Gauge data object
class GaugeData(ClawData):
    r""""""

    @property
    def gauge_numbers(self):
        if len(self.gauges) == 1:
            return [self.gauges[0][0]]
        else:
            return [gauge[0] for gauge in self.gauges]

    def __init__(self):
        super(GaugeData,self).__init__()

        self.add_attribute('gauges',[])

    def __str__(self):
        output = "Gauges: %s\n" % len(self.gauges)
        for gauge in self.gauges:
            output = "\t".join((output,"%4i:" % gauge[0]))
            output = " ".join((output,"%19.10e" % gauge[1]))
            output = " ".join((output,"%17.10e" % gauge[2]))
            output = " ".join((output,"%13.6e" % gauge[3]))
            output = " ".join((output,"%13.6e\n" % gauge[4]))
        return output

    def write(self,out_file='gauges.data',data_source='setrun.py'):
        r"""Write out gague information data file."""

        # Check to make sure we have only unique gauge numebrs
        if len(self.gauges) > 0:
            if len(self.gauge_numbers) != len(set(self.gauge_numbers)):
                raise Exception("Non unique gauge numbers specified.")

        # Write out gauge data file
        self.open_data_file(out_file,data_source)
        self.data_write(name='ngauges',value=len(self.gauges))
        for gauge in self.gauges:
            self._out_file.write("%4i %19.10e  %17.10e  %13.6e  %13.6e\n" % tuple(gauge))
        self.close_data_file()

    def read(self,data_path="./",file_name='gauges.data'):
        r"""Read gauge data file"""
        path = os.path.join(data_path, file_name)
        gauge_file = open(path,'r')

        # Read past comments and blank lines
        header_lines = 0
        ignore_lines = True
        while ignore_lines:
            line = gauge_file.readline()
            if line[0] == "#" or len(line.strip()) == 0:
                header_lines += 1
            else:
                break

        # Read number of gauges, should be line that was last read in
        num_gauges = int(line.split()[0])

        # Read in each gauge line
        for n in xrange(num_gauges):
            line = gauge_file.readline().split()
            self.gauges.append([int(line[0]),float(line[1]),float(line[2]),
                                             float(line[3]),float(line[4])])


#  Gauge data objects
# ==============================================================================

class UserData(ClawData):
    r"""
    Object that will be written out to user file such as setprob.data, as
    determined by the fname attribute.
    """

    def __init__(self, fname):

        super(UserData,self).__init__()

        # Create attributes without adding to attributes list:

        # file to be read by Fortran for this data:
        object.__setattr__(self,'__fname__',fname)

        # dictionary to hold descriptions:
        object.__setattr__(self,'__descr__',{})

    def add_param(self,name,value,descr=''):
         self.add_attribute(name,value)
         descr_dict = self.__descr__
         descr_dict[name] = descr

    def write(self,data_source='setrun.py'):
        super(UserData,self).write(self.__fname__, data_source)
