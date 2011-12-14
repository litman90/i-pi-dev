import math, time
import numpy as np
from utils.depend import *
from utils.units import *
from utils.mathtools import eigensystem_ut3x3, invert_ut3x3, exp_ut3x3, det_ut3x3
from engine.thermostats import Thermostat

class Barostat(dobject): 
   def __init__(self, pext=0.0, sext = None, dt = None, temp = None, thermostat=Thermostat()):

      # This kind of stretches the concept of synced dependencies: sext holds more information than pext but....
      sync_ext=synchronizer()
      dset(self,"sext",depend_array(name='sext', value=numpy.zeros((3,3)), deps=depend_sync(synchro=sync_ext, func={"pext" : self.p2s} )) )
      dset(self,"pext",depend_value(name='pext', value=0.0, deps=depend_sync(synchro=sync_ext, func={"sext" : self.s2p} )) )            
      if sext is None:
         self.pext=pext
      else:
         self.sext=sext
      
      self.thermostat=thermostat   
      # binds options for dt and temperature of the thermostat to those in the barostat
     
      dset(self,"dt",depend_value(name='dt'))
      if dt is None: self.dt=2.0*self.thermostat.dt
      else: self.dt=dt
      dset(self.thermostat,"dt",   #this involves A LOT of piping
         depend_value(name="dt",deps=depend_func(func=self.get_halfdt,dependencies=[depget(self,"dt")],dependants=depget(self.thermostat,"dt")._dependants) ) )
           
      #temp
      dset(self, "temp", dget(self.thermostat,"temp"))
      if not temp is None: self.temp=temp
      
      self.timer=0.0
      
   def get_halfdt(self):  return self.dt*0.5
         
   def bind(self, atoms, cell, force):
      """Binding function which prepares most of the stuff which will be necessary for a barostat"""
      self.atoms=atoms
      self.cell=cell
      self.force=force

      dset(self,"pot",depend_value(name='pot', deps=depend_func(func=self.get_pot, 
          dependencies=[ depget(cell,"V0"), depget(cell,"strain"), depget(self,"sext")  ]  ) ) )            
      dset(self,"piext",depend_value(name='piext', deps=depend_func(func=self.get_piext, 
          dependencies=[ depget(cell,"V0"), depget(cell,"V"), depget(cell,"h"), depget(cell,"ih0"), depget(cell,"strain"), depget(self,"sext")  ]  ) ) )     
      dset(self,"stress",depend_value(name='stress', deps=depend_func(func=self.get_stress, 
          dependencies=[ depget(atoms,"kstress"), depget(cell,"V"), depget(force,"vir")  ]  ) ) )     
      dset(self,"press",depend_value(name='press', deps=depend_func(func=self.get_press, 
          dependencies=[ depget(self,"stress") ]  ) ) )
                
   def s2p(self): return np.trace(self.sext)/3.0
   def p2s(self): return self.pext*np.identity(3)
      
   def pstep(self): pass
   def qstep(self): pass   
      
   def step(self):
      """Dummy atoms barostat step""" 
      self.thermostat.step()
      self.pstep()
      self.qstep()
      self.pstep()
      self.thermostat.step()
      
   def get_pot(self):
      """Calculates the elastic strain energy of the cell"""
      return self.cell.V0*numpy.trace(numpy.dot(self.sext, self.cell.strain))

   def get_piext(self):
      """Calculates the external stress tensor"""
      root = numpy.dot(self.cell.h, self.cell.ih0).view(np.ndarray)
      pi = numpy.dot(root, self.sext)
      
      pi = numpy.dot(pi, numpy.transpose(root))
      pi *= self.cell.V0/self.cell.V
      return pi
      
   def get_stress(self):
      """Calculates the elastic strain energy of the cell"""
      
      return (self.atoms.kstress+self.force.vir)/self.cell.V    
#TODO  also include a possible explicit dependence of U on h

   def get_press(self):
      return np.trace(self.stress)/3.0

class BaroFlexi(Barostat):


   def bind(self, atoms, cell, force):
      super(BaroFlexi,self).bind(atoms,cell,force)
      self.thermostat.bind(cell=self.cell)

#   def exp_p(self):
#      dist_mat = (self.cell.p*self.dt/self.cell.m).view(np.ndarray)
##      exp_mat=matrix_exp(dist_mat);  neg_exp_mat=matrix_exp(-1.0*dist_mat);       
#      eig, eigvals = eigensystem_ut3x3(dist_mat)
#      i_eig = invert_ut3x3(eig)

#      exp_mat = numpy.zeros((3,3))
#      neg_exp_mat = numpy.zeros((3,3))
#      for i in range(3):
#         exp_mat[i,i] = math.exp(eigvals[i])
#         neg_exp_mat[i,i] = math.exp(-eigvals[i])

#      exp_mat = numpy.dot(eig, exp_mat)
#      exp_mat = numpy.dot(exp_mat, i_eig)
#         
#      neg_exp_mat = numpy.dot(eig, neg_exp_mat)
#      neg_exp_mat = numpy.dot(neg_exp_mat, i_eig)

#      em2=exp_ut3x3(dist_mat)
#      iem=exp_ut3x3(-dist_mat)      
#      return exp_mat, neg_exp_mat

   def pstep(self):
      
      dthalf = self.dt*0.5
      dthalf2=dthalf**2/2.0
      dthalf3=dthalf**3/3.0     

      L = numpy.zeros((3,3))
      for i in range(3): L[i,i] = 3.0 - i
      
      #step on the cell velocities - first term, which only depends on "cell" quantities
      self.cell.p += dthalf*(self.cell.V*(self.stress - self.piext) + 2.0*Constants.kb*self.thermostat.temp*L)       
     # pdb.set_trace()

      #now must compute the terms depending on outer products of f and p
      f = self.force.f.view(np.ndarray)
      m = self.atoms.m.view(np.ndarray)
      p = self.atoms.p.view(np.ndarray)  # this strips the dependency checks from p, making it inexpensive to scan through ...
      nat=self.atoms.natoms
            
      #time.doprint=True
#      for i in range(nat):
#         fi=f[3*i:3*(i+1)]; pi=p[3*i:3*(i+1)]; cpi=0.0
#         for j in range(3): 
#            for k in range(j,3):
#               cpi[j,k] += (dthalf2*(fi[j]*pi[k] + fi[k]*pi[j])+ dthalf3*fi[k]*fi[j])
#         cp+=cpi/m[i]
#         cp+=(dthalf2*(np.outer(fi,pi) + np.outer(pi,fi))+ dthalf3*np.outer(fi,fi))/m[i]

      # for mysterious reasons, the expression below is orders of magnitude faster than the above.
      fx=f[0:3*nat:3];       fy=f[1:3*nat:3];       fz=f[2:3*nat:3];
      fxm=fx/m;              fym=fy/m;              fzm=fz/m;             
      px=p[0:3*nat:3];       py=p[1:3*nat:3];       pz=p[2:3*nat:3];        
      
      cp=numpy.zeros((3,3),float)
      cp[0,0]=dthalf2*2.0*np.dot(fxm,px) + dthalf3*np.dot(fx,fxm)
      cp[1,1]=dthalf2*2.0*np.dot(fym,py) + dthalf3*np.dot(fy,fym)
      cp[2,2]=dthalf2*2.0*np.dot(fzm,pz) + dthalf3*np.dot(fz,fzm)
      cp[0,1]=dthalf2*(np.dot(fxm,py)+np.dot(px,fym)) + dthalf3*np.dot(fx,fym)
      cp[0,2]=dthalf2*(np.dot(fxm,pz)+np.dot(px,fzm)) + dthalf3*np.dot(fx,fzm)
      cp[1,2]=dthalf2*(np.dot(fym,pz)+np.dot(py,fzm)) + dthalf3*np.dot(fy,fzm)            
      
      self.cell.p+=cp      
      self.atoms.p += f*dthalf      
      
   def qstep(self):
      """Takes the atom positions, velocities and forces and integrates the 
         equations of motion forward by a step dt"""
      #(self.cell.p*self.dt/self.cell.m).view(np.ndarray)
      self.timer-=time.clock()
      
      vel_mat = (self.cell.p/self.cell.m).view(np.ndarray)

      vel_mat*=self.dt
      exp_mat=exp_ut3x3(vel_mat)
      neg_exp_mat = invert_ut3x3(exp_mat)
      sinh_mat = 0.5*(exp_mat - neg_exp_mat)
      ips_mat = numpy.dot( sinh_mat, invert_ut3x3(vel_mat) )

      nat=len(self.atoms)
      p = self.atoms.p.view(np.ndarray).copy().reshape((nat,3)) 
      q = self.atoms.q.view(np.ndarray).copy().reshape((nat,3))   # this strips the dependency checks off p and q, making it inexpensive to scan through ...
      m3 = self.atoms.m3.view(np.ndarray).copy().reshape((nat,3))       

#      k=0
#      for i in range(nat):
#         kn=k+3  
#         q[k:kn] = numpy.dot(exp_mat, q[k:kn]) + numpy.dot(ips_mat, p[k:kn]/m[i])
#         p[k:kn] = numpy.dot(neg_exp_mat, p[k:kn])
#         k=kn
#      depget(self.atoms,"p").taint(taintme=False)  # .. but one must remember to taint it manually!
#      depget(self.atoms,"q").taint(taintme=False)  # .. but one must remember to taint it manually!
      
      #pdb.set_trace()
      
      # quick multiplication  by making it in matrix form
      q=numpy.dot(q,exp_mat.T)+numpy.dot(p/m3,ips_mat.T)
      p=numpy.dot(p,neg_exp_mat.T)

      # assigns back to actual storage
      self.atoms.q=q.reshape(3*nat)
      self.atoms.p=p.reshape(3*nat)
                    
      self.cell.h=numpy.dot(exp_mat, self.cell.h)
      self.timer+=time.clock()
      
class BaroRigid(Barostat):

   def get_pot(self):
      """Calculates the elastic strain energy of the cell"""
      return self.cell.V*self.pext
      
   def bind(self, atoms, cell, force):
      super(BaroRigid,self).bind(atoms, cell, force)
      self.thermostat.bind(pm=(self.cell.P, self.cell.M))
      dset(self,"pot",depend_value(name='pot', deps=depend_func(func=self.get_pot, 
          dependencies=[ depget(self.cell,"V"), depget(self,"pext")  ]  ) ) )            
      
   def pstep(self):
      
      dthalf = self.dt*0.5
      dthalf2=dthalf**2/2.0
      dthalf3=dthalf**3/3.0     
      
      #step on the cell velocities - first term, which only depends on "cell" quantities      
      #pV=np.trace(numpy.dot(self.cell.ih,self.cell.p))*self.cell.V
      #print "check start ",self.pV, np.trace(numpy.dot(self.cell.ih,self.cell.p))*self.cell.V
      self.cell.P += dthalf*3.0*(self.cell.V*(self.press - self.pext) + 2.0*Constants.kb*self.temp)


      #now must compute the terms depending on outer products of f and p
      f = self.force.f.view(np.ndarray)
      m = self.atoms.m3.view(np.ndarray)
      p = self.atoms.p.view(np.ndarray)  # this strips the dependency checks from p, making it inexpensive to scan through ...
            
      self.cell.P+=dthalf2*np.dot(p,f/m)+dthalf3*np.dot(f,f/m)
   
      self.atoms.p += f*dthalf      
      
           
   def qstep(self):
      """Takes the atom positions, velocities and forces and integrates the 
         equations of motion forward by a step dt"""
      eta = self.cell.P[0]/self.cell.m
      exp, neg_exp = ( math.exp(eta*self.dt), math.exp(-eta*self.dt))
      sinh = 0.5*(exp - neg_exp)

      
      p = self.atoms.p.view(np.ndarray) 
      q = self.atoms.q.view(np.ndarray)   # this strips the dependency checks off p and q, making it inexpensive to scan through ...
      m = self.atoms.m3.view(np.ndarray)      
      q*=exp
      q+=(sinh/eta)* p/m
      p *= neg_exp

      depget(self.atoms,"p").taint(taintme=False)  # .. but one must remember to taint it manually!
      depget(self.atoms,"q").taint(taintme=False)  # .. but one must remember to taint it manually!

      self.cell.V*=exp**3
              