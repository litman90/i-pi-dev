import numpy as np
import math
from utils.depend import *
from utils.mathtools import det_ut3x3, invert_ut3x3
from utils import units
import pdb

class Cell(dobject):
   """Represents the simulation cell in a periodic system
      Contains: h = lattice vector matrix, p = lattice momentum matrix (NST),
      pc = lattice scalar momentum (NPT), w = barostat mass, pext = external 
      pressure tensor, V = volume, ih = inverse lattice matrix, 
      (h0, ih0, V0) = as above, but for reference cell (pext = 0), 
      kin = kinetic energy, pot = strain potential, 
      strain = strain tensor, piext = external stress tensor
      Initialised by: cell = Cell(h, w, h0, pext)
      h is the lattice vector matrix
      w = barostat mass, default = 1.0
      h0 = reference cell, default = h
      pext = external pressure tensor, default = 0"""

   def __init__(self, h = numpy.identity(3, float), m=1.0):      
     
      #un-dependent properties
      dset(self,"h",depend_array(name = 'h', value = h) )
      dset(self,"p",depend_array(name = 'p', value = numpy.zeros((3,3),float)) )
      dset(self,"m",depend_value(name = "m", value = m) )

      #reference cell      
      h0=numpy.array(h,copy=True)
      dset(self,"h0",depend_array(name = 'h0', value = h0 ) )
            
      dset(self,"ih" ,  depend_array(name = "ih", value = numpy.zeros((3,3),float), deps=depend_func(func=self.get_ih, dependencies=[depget(self,"h")])))
      dset(self,"ih0" , depend_array(name = "ih0", value = numpy.zeros((3,3),float), deps=depend_func(func=self.get_ih0, dependencies=[depget(self,"h0")])) )
      dset(self,"strain", depend_value(name = "strain", deps=depend_func(func=self.get_strain, dependencies=[depget(self,"h"),depget(self,"h0")])) )
            
   def get_ih(self):
      """Inverts a 3*3 (upper-triangular) cell matrix"""
      return invert_ut3x3(self.h)      
   def get_ih0(self):      return invert_ut3x3(self.h0)      

   def get_strain(self):
      """Computes the strain tensor from the unit cell and reference cell"""

      root = numpy.dot(self.h, self.ih0).view(np.ndarray)
      eps = numpy.dot(numpy.transpose(root), root) - numpy.identity(3, float)
      eps *= 0.5
      return eps
      
   def apply_pbc(self, atom):
      """Uses the minimum image convention to return a particle to the
         unit cell"""
      s=numpy.dot(self.ih,atom.q)
      for i in range(3):
         s[i] = s[i] - round(s[i])
      return numpy.dot(self.h,s)

   def minimum_distance(self, atom1, atom2):
      """Takes two atoms and tries to find the smallest vector between two 
         images. This is only rigorously accurate in the case of a cubic cell,
         but gives the correct results as long as the cut-off radius is defined
         as smaller than the smallest width between parallel faces."""

      s=numpy.dot(self.ih,atom1.q-atom2.q)
      
      for i in range(3):
         s[i] -= round(s[i])
         
      return numpy.dot(self.h, s)


class CellFlexi(Cell):
   def __init__(self, h = numpy.identity(3, float), h0=None, m=1.0):    
      super(CellFlexi,self).__init__(h=h, m=m)
      # must redefine most values to set up sync
      # interface for accessing the cell degrees of freedom as flat size-6 arrays
      sync_h=synchronizer();    sync_p=synchronizer();
      dset(self,"h6",depend_array(name="h6", value=numpy.zeros(6,float), deps=depend_sync(func={"h":self.htoh6}, synchro=sync_h) ) )      
      dset(self,"p6",depend_array(name="p6", value=numpy.zeros(6,float), deps=depend_sync(func={"p":self.ptop6}, synchro=sync_p) ) )  
                
      #un-dependent properties
      dset(self,"h",depend_array(name = 'h', value = h, deps=depend_sync(func={"h6":self.h6toh}, synchro=sync_h) ) )
      dset(self,"p",depend_array(name = 'p', value = numpy.zeros((3,3),float), deps=depend_sync(func={"p6":self.p6top}, synchro=sync_p) ) )
      dset(self,"m6",depend_array(name= "m6", value=numpy.zeros(6,float), deps=depend_func(func=self.mtom6, dependencies=[depget(self,"m")]) ) )      

      #since we redefined h, we must update definitions of ih and strain
      dset(self,"ih" ,  depend_array(name = "ih", value = numpy.zeros((3,3),float), deps=depend_func(func=self.get_ih, dependencies=[depget(self,"h")])) )
      dset(self,"strain", depend_value(name = "strain", deps=depend_func(func=self.get_strain, dependencies=[depget(self,"h"),depget(self,"h0")])) )
      
      #reference cell
      if not h0 is None:  self.h0=h0
      
      dset(self,"V",depend_value(name = 'V', deps=depend_func(func=self.get_volume, dependencies=[depget(self,"h")])) )
      dset(self,"V0",depend_value(name = 'V0', deps=depend_func(func=self.get_volume0, dependencies=[depget(self,"h0")])) )
      
      dset(self,"kin",    depend_value(name = "kin", deps=depend_func(func=self.get_kin, dependencies=[depget(self,"p"),depget(self,"m")])) )
      

   # conversion between the different representations of p and h
   def htoh6(self):  h6=numpy.zeros(6, float);    h=self.h.view(np.ndarray);    h6[0:3]=h[0,0:3]; h6[3:5]=h[1,1:3]; h6[5:6]=h[2,2];  return h6
   def h6toh(self):  h=numpy.zeros((3,3), float); h6=self.h6.view(np.ndarray);  h[0,0:3]=h6[0:3]; h[1,1:3]=h6[3:5]; h[2,2]=h6[5:6];  return h
   def ptop6(self):  p6=numpy.zeros(6, float);    p=self.p.view(np.ndarray);    p6[0:3]=p[0,0:3]; p6[3:5]=p[1,1:3]; p6[5:6]=p[2,2];  return p6
   def p6top(self):  p=numpy.zeros((3,3), float); p6=self.p6.view(np.ndarray);  p[0,0:3]=p6[0:3]; p[1,1:3]=p6[3:5]; p[2,2]=p6[5:6];  return p
   
   def mtom6(self):  m6=numpy.zeros(6, float);    m6=self.m;  return m6

            
   def get_volume(self):
      """Calculates the volume of the unit cell, assuming an upper-triangular
         lattice vector matrix"""         
      return det_ut3x3(self.h)

   def get_volume0(self):      return det_ut3x3(self.h0)
            
   def get_kin(self):
      """Calculates the kinetic energy of the cell from the cell parameters"""
      p6=self.p6.view(np.ndarray)   # strips the deps object from p6
      return np.dot(p6,p6)/(2.0*self.m)
      
      
class CellRigid(Cell):
   def __init__(self, h = numpy.identity(3, float), m=1.0):    
      super(CellRigid,self).__init__(h, m)

      #reference cell volume
      dset(self,"V0",depend_value(name = 'V0', deps=depend_func(func=self.get_volume0, dependencies=[depget(self,"h0")])) )
      dset(self,"V",depend_value(name = 'V', value=self.get_volume0()) )

      # here h0 is taken as the reference cell, and the real dynamical variable is the volume. Hence, h is a derived quantity            
      dset(self,"h",depend_array(name = 'h', value = h, deps=depend_func(func=self.Vtoh, dependencies=[depget(self,"V"),depget(self,"h0")]) ) )
      dset(self,"ih" ,  depend_array(name = "ih", value = numpy.zeros((3,3),float), deps=depend_func(func=self.get_ih, dependencies=[depget(self,"h")])) )      


      # rate of volume change times m ("volume momentum")      
      dset(self,"P",depend_array(name = 'P', value=np.zeros(1,float)) )
      # array-like access to the mass (useful for thermostatting)
      dset(self,"M",depend_array(name="M", value=np.zeros(1,float), deps=depend_func(func=self.mtoM, dependencies=[depget(self,"m")]) ) )                  
      
      # this must be well-thought
      dset(self,"p",depend_array(name = 'p', value = numpy.zeros((3,3),float), deps=depend_func(func=self.Ptop, dependencies=[depget(self,"P"),depget(self,"h0")]) ) )

      dset(self,"kin",    depend_value(name = "kin", deps=depend_func(func=self.get_kin, dependencies=[depget(self,"P"),depget(self,"m")])) )
      
   def mtoM(self): return np.identity(1)*self.m
   def Vtoh(self): return self.h0.view(np.ndarray).copy()*(self.V/self.V0)**(1.0/3.0)
   def Ptop(self): pass

   def get_volume0(self): return det_ut3x3(self.h0)
            
   def get_kin(self):   return self.P[0]**2/(2.0*self.m)
   
   