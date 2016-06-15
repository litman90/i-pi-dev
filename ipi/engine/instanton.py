"""Contains the classes that deal with the different dynamics required in
different types of ensembles.

Copyright (C) 2013, Joshua More and Michele Ceriotti

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program. If not, see <http.//www.gnu.org/licenses/>.
"""

__all__=['Instanton']

import numpy as np
import time

# ADD ALL IMPORTS THAT ARE NECESSARY (from geop and so on)
from ipi.engine.motion.motion import Motion
from ipi.utils.depend import *
from ipi.utils import units
from ipi.utils.softexit import softexit
from ipi.utils.mintools import min_brent, min_approx, BFGS, L_BFGS, L_BFGS_nls
from ipi.utils.messages import verbosity, warning, info

class Instanton(GeopMover):
    """Dynamic matrix calculation routine by finite difference.
    """
# CHANGE THESE KEYWORDS TO BE CONSISTENT WITH GEOPMOVER
    def __init__(self, mode, max_step=0.3, g_tol=0.001, prefix=""):   
                 
        """Initialises InstantonMover.
        Args:
 
        """

        super(InstantonMover,self).__init__(fixcom=fixcom, fixatoms=fixatoms)
      
        #Finite difference option.
        self.mode = mode
        self.maxstep = max_step
        self.gtol = g_tol
#        self.frefine = False
#        self.U = None
#        self.V = None
        self.prefix = prefix
        if self.prefix == "":
            self.prefix = "INSTANTON"
   
    def bind(self, ens, beads, nm, cell, bforce, prng):

        super(InstantonMover,self).bind(ens, beads, nm, cell, bforce, prng)


        #Initialises a 3*number of atoms X 3*number of atoms dynamic matrix.
        if(self.dynmatrix.size  != (beads.q.size * beads.q.size)):
            if(self.dynmatrix.size == 0):
                self.dynmatrix=np.zeros((beads.q.size, beads.q.size), float)
                self.dynmatrix_r=np.zeros((beads.q.size, beads.q.size), float)
            else:
                raise ValueError("Force constant matrix size does not match system size")
 
        self.dbeads = self.beads.copy()
        self.dcell = self.cell.copy()
        self.dforces = self.forces.copy(self.dbeads, self.dcell)
        #  TODO this should probably be made into a depend object, or taken from beads that have a sm3 object
        self.ism = 1/np.sqrt(depstrip(beads.m3[-1]))

    def step(self, step=None):
    # This is what will calculate the instanton  
    # For example to print all and exit:
    #            if not self.frefine:            
    #            self.printall(self.prefix, rdyn, self.deltaw)
    #            if self.mode=="std":
    #                softexit.trigger("Dynamic matrix is calculated. Exiting simulation")  

    def printall(self, prefix):


