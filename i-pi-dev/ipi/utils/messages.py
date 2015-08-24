"""Classes to print info, warnings and errors to standard output during the simulation."""

# This file is part of i-PI.
# i-PI Copyright (C) 2014-2015 i-PI developers
# See the "licenses" directory for full license information.


import traceback
import sys


__all__ = ['Verbosity', 'verbosity',' help', 'banner', 'info', 'warning']


VERB_QUIET  = 0
VERB_LOW    = 1
VERB_MEDIUM = 2
VERB_HIGH   = 3
VERB_DEBUG  = 4

class Verbosity(object):
   """Class used to determine what to print to standard output.

   Attributes:
      level: Determines what level of output to print.
   """

   lock = False
   level = "low"

   def __getattr__(self, name):
      """Determines whether a certain verbosity level is
      less than or greater than the stored value.

      Used to decide whether or not a certain info or warning string
      should be output.

      Args:
         name: The verbosity level at which the info/warning string
            will be output.
      """

      if name is "quiet":
         return self.level >= VERB_QUIET
      elif name is "low":
         return self.level >= VERB_LOW
      elif name is "medium":
         return self.level >= VERB_MEDIUM
      elif name is "high":
         return self.level >= VERB_HIGH
      elif name is "debug":
         return self.level >= VERB_DEBUG
      else: return super(Verbosity,self).__getattr__(name)

   def __setattr__(self, name, value):
      """Sets the verbosity level

      Args:
         name: The name of what to set. Should always be 'level'.
         value: The value to set the verbosity to.

      Raises:
         ValueError: Raised if either the name or the level is not
            a valid option.
      """

      if name == "level":
         if self.lock : return # do not set the verbosity level if this is locked
         if value == "quiet":
            level = VERB_QUIET
         elif value == "low":
            level = VERB_LOW
         elif value == "medium":
            level = VERB_MEDIUM
         elif value == "high":
            level = VERB_HIGH
         elif value == "debug":
            level = VERB_DEBUG
         else:
            raise ValueError("Invalid verbosity level " + str(value) + " specified.")
         super(Verbosity,self).__setattr__("level", level)
      else: super(Verbosity,self).__setattr__(name, value)


verbosity = Verbosity()

def help():
   """Prints out a help string."""

   print """usage:  %s input """%sys.argv[0]

def banner():
   """Prints out a banner."""

   print """
 ____       ____       ____       ____
/    \     /    \     /    \     /    \\
|  #################################  |
\__#_/     \____/     \____/     \_#__/
   #    _        _______  _____    #
   #   (_)      |_   __ \|_   _|   #      -*-     Development version    -*-
   #   __  ______ | |__) | | |     #
   Y  [  ||______||  ___/  | |     #      A Python interface for (ab initio)
  0 0  | |       _| |_    _| |_    #      (path integral) molecular dynamics.
   #  [___]     |_____|  |_____|   #
 __#_       ____       ____       _#__
/  # \     /    \     /    \     / #  \\
|  #################################  |
\____/     \____/     \____/     \____/

   """


def info(text="", show=True):
   """Prints a message.

   Args:
      text: The text of the information message.
      show: A boolean describing whether or not the message should be
         printed.
   """

   if not show:
      return
   print text

def warning(text="", show=True):
   """Prints a warning message.

   Same as info, but with a "!W!" prefix and optionally printing a stack trace.

   Args:
      text: The text of the information message.
      show: A boolean describing whether or not the message should be
         printed.
   """

   if not show:
      return
   if verbosity.debug:
      traceback.print_stack(file=sys.stdout)
   print " !W! " + text
