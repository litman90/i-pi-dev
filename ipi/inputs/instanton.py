"""Deals with creating the ensembles class.

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

Inputs created by Michele Ceriotti and Benjamin Helfrecht, 2015

Classes:
   InputGeop: Deals with creating the Geop object from a file, and
      writing the checkpoints.
"""

import numpy as np
import ipi.engine.initializer
from ipi.engine.motion import *
from ipi.utils.inputvalue import *
from ipi.inputs.initializer import *
from ipi.utils.units import *

__all__ = ['InputInstanton']

class InputInstanton(InputDictionary):

	    """Instanton calculation options.
    
       Contains options related to calculations of instantons. 

    """

    attribs={"mode"  : (InputAttribute, {"dtype"   : str, 
                                    "help"    : "The type of instanton to be calculated",
                                    "options" : ["min", "saddle"]}) }
    fields = { 
                "max_step"  : (InputValue, {"dtype"   : float, "default": 0.3, 
                                    "help"    : "Maximum step."
                                    }), 
                "g_tol"  : (InputValue, {"dtype"   : float, "default": 0.000, 
                                    "help"    : "The finite deviation in energy used to compute deribvative of force."
                                    }),              
             }
                   
 #   dynamic = {  }

    default_help = "Fill in."
    default_label = "INSTANTON"

    def store(self, instanton):
        if phonons  == {}: return
        self.mode.store(instanton.mode)
        self.max_step.store(instaton.maxstep)
        self.g_tol.store(instanton.gtol)        
        
    def fetch(self):		
        rv = super(InputInstaton,self).fetch()
        rv["mode"] = self.mode.fetch()        
        return rv
