# -*- coding: utf-8 -*-
# Copyright (c) 2010, Almar Klein
#
# Visvis is distributed under the terms of the (new) BSD License.
# The full license can be found in 'license.txt'.

""" Module misc

Various things are defined here that did not fit nicely in any
other module. 

This module is also meant to be imported by many
other visvis modules, and therefore should not depend on other
visvis modules.

"""

import sys, os, time
from visvis import ssdf
import OpenGL.GL as gl


## For info about OpenGL version


# To store openGl info
_glInfo = [None]*4

def getOpenGlInfo():
    """ getOpenGlInfo()
    
    Get information about the OpenGl version on this system. 
    Returned is a tuple (version, vendor, renderer, extensions) 
    Note that this function will return 4 Nones if the openGl 
    context is not set.
    
    """
    
    if not _glInfo[0]:
        _glInfo[0] = gl.glGetString(gl.GL_VERSION)
        _glInfo[1] = gl.glGetString(gl.GL_VENDOR)
        _glInfo[2] = gl.glGetString(gl.GL_RENDERER)
        _glInfo[3] = gl.glGetString(gl.GL_EXTENSIONS)
    return tuple(_glInfo)

_glLimitations = {}
def getOpenGlCapable(version, what=None):
    """ getOpenGlCapable(version, what)
    
    Returns True if the OpenGl version on this system is equal or higher 
    than the one specified and False otherwise.
    
    If False, will display a message to inform the user, but only the first 
    time that this limitation occurs (identified by the second argument).
    
    """
    
    # obtain version of system
    curVersion = _glInfo[0]
    if not curVersion:
        curVersion, dum1, dum2, dum3 = getOpenGlInfo()
        if not curVersion:
            return False # OpenGl context not set, better safe than sory
    
    # make sure version is a string
    if isinstance(version, (int,float)):
        version = str(version)
    
    # test
    if curVersion >= version :
        return True
    else:
        # print message?
        if what and (what not in _glLimitations):
            _glLimitations[what] = True
            tmp = "Warning: the OpenGl version on this system is too low "
            tmp += "to support " + what + ". "
            tmp += "Try updating your drivers or buy a new video card."
            print tmp
        return False


## Decorators


def Property(function):
    """ Property(function)
    
    A property decorator which allows to define fget, fset and fdel
    inside the function.
    
    Note that the class to which this is applied must inherit from object!
    Code from George Sakkis: http://code.activestate.com/recipes/410698/
    
    """
    # Init
    keys = 'fget', 'fset', 'fdel'
    func_locals = {'doc':function.__doc__}
    
    # Define function to probe the special methods defined in function
    def probeFunc(frame, event, arg):
        if event == 'return':
            locals = frame.f_locals
            func_locals.update(dict((k,locals.get(k)) for k in keys))
            sys.settrace(None)
        return probeFunc
    
    # Probe the function (fills func_locals)
    sys.settrace(probeFunc)
    function()
    
    # Done
    return property(**func_locals)


def PropWithDraw(function):
    """ PropWithDraw(function)
    
    A property decorator which allows to define fget, fset and fdel
    inside the function.
    
    Same as Property, but callas self.Draw() when using fset.
    
    """
    # Init
    keys = 'fget', 'fset', 'fdel'
    func_locals = {'doc':function.__doc__}
    
    # Define function to probe the special methods defined in function
    def probeFunc(frame, event, arg):
        if event == 'return':
            locals = frame.f_locals
            func_locals.update(dict((k,locals.get(k)) for k in keys))
            sys.settrace(None)
        return probeFunc
    
    # Probe the function (fills func_locals)
    sys.settrace(probeFunc)
    function()
    
    # Replace fset
    fset = func_locals.get('fset',None)
    def fsetWithDraw(self, *args):
        fset(self, *args)
        self.Draw()
        #print fset._propname, self, time.time()
    if fset:
        fset._propname = function.__name__
        func_locals['fset'] = fsetWithDraw
    
    # Done
    return property(**func_locals)


def DrawAfter(function):
    """ DrawAfter(function)
    
    Decorator for methods that make self.Draw() be called right after
    the function is called. 
    
    """
    def newFunc(self, *args, **kwargs):
        function(self, *args, **kwargs)
        if hasattr(self, 'Draw'):
            self.Draw()
    newFunc.__doc__ = function.__doc__
    return newFunc


## The range class


class Range(object):
    """ Range(min=0, max=0)
    
    Represents a range (a minimum and a maximum ). Can also be instantiated
    using a tuple.
    
    If max is set smaller than min, the min and max are flipped.    
    
    """
    def __init__(self, min=0, max=1):
        self.Set(min,max)
    
    def Set(self, min=0, max=1):
        """ Set the values of min and max with one call. 
        Same signature as constructor.
        """
        if isinstance(min, Range):
            min, max = min.min, min.max
        elif isinstance(min, (tuple,list)):
            min, max = min[0], min[1]        
        self._min = float(min)
        self._max = float(max)
        self._Check()
    
    @property
    def range(self):        
        return self._max - self._min
    
    @Property # visvis.Property
    def min():
        """ Get/Set the minimum value of the range. """
        def fget(self):
            return self._min
        def fset(self,value):
            self._min = float(value)
            self._Check()
    
    @Property # visvis.Property
    def max():
        """ Get/Set the maximum value of the range. """
        def fget(self):
            return self._max
        def fset(self,value):
            self._max = float(value)
            self._Check()
    
    def _Check(self):
        """ Flip min and max if order is wrong. """
        if self._min > self._max:
            self._max, self._min = self._min, self._max
    
    def Copy(self):
        return Range(self.min, self.max)
        
    def __repr__(self):
        return "<Range %1.2f to %1.2f>" % (self.min, self.max)


## Transform classes for wobjects
    
    
class Transform_Base(object):
    """ Transform_Base
    
    Base transform object. 
    Inherited by classes for translation, scale and rotation.
    
    """
    pass
    
class Transform_Translate(Transform_Base):
    """ Transform_Translate(dx=0.0, dy=0.0, dz=0.0)
    
    Translates the wobject. 
    
    """
    def __init__(self, dx=0.0, dy=0.0, dz=0.0):
        self.dx = dx
        self.dy = dy
        self.dz = dz

class Transform_Scale(Transform_Base):
    """ Transform_Scale(sx=1.0, sy=1.0, sz=1.0)
    
    Scales the wobject. 
    
    """
    def __init__(self, sx=1.0, sy=1.0, sz=1.0):
        self.sx = sx
        self.sy = sy
        self.sz = sz

class Transform_Rotate(Transform_Base):
    """ Transform_Rotate( angle=0.0, ax=0, ay=0, az=1, angleInRadians=None) 
    
    Rotates the wobject. Angle is in degrees. 
    Use angleInRadians to specify the angle in radians, 
    which is then converted in degrees. 
    """
    def __init__(self, angle=0.0, ax=0, ay=0, az=1, angleInRadians=None):
        if angleInRadians is not None:
            angle = angleInRadians * 180 / np.pi 
        self.angle = angle
        self.ax = ax
        self.ay = ay
        self.az = az

## Colour stuff

# Define named colors
colorDict = {}
colorDict['black']  = colorDict['k'] = (0,0,0)
colorDict['white']  = colorDict['w'] = (1,1,1)
colorDict['red']    = colorDict['r'] = (1,0,0)
colorDict['green']  = colorDict['g'] = (0,1,0)
colorDict['blue']   = colorDict['b'] = (0,0,1)
colorDict['cyan']   = colorDict['c'] = (0,1,1)
colorDict['yellow'] = colorDict['y'] = (1,1,0)
colorDict['magenta']= colorDict['m'] = (1,0,1)

def getColor(value, descr='getColor'):
    """ getColor(value, descr='getColor')
    
    Make sure a value is a color. If a character is given, returns the color
    as a tuple.
    
    """
    tmp = ""
    if not value:
        value = None
    elif isinstance(value, (str, unicode)):
        if value not in 'rgbycmkw':
            tmp = "string color must be one of 'rgbycmkw' !"
        else:
            value = colorDict[value]
    elif isinstance(value, (list, tuple)):
        if len(value) != 3:
            tmp = "tuple color must be length 3!"                
        value = tuple(value)
    else:
        tmp = "color must be a three element tuple or a character!"
    # error or ok?
    if tmp:
        raise ValueError("Error in %s: %s" % (descr, tmp) )        
    return value


## More functions ...

def isFrozen():
    """ isFrozen
    
    Returns whether this is a frozen application
    (using bbfreeze or py2exe) by finding out what was
    the executable name to start the application.
    
    """
    ex = os.path.split(sys.executable)[1]
    ex = os.path.splitext(ex)[0]
    if ex.lower().startswith('python'):
        return False
    else:
        return True


def getResourceDir():
    """ getResourceDir()
    
    Get the directory to the visvis resources. 
    
    """
    if isFrozen():
        path =  os.path.abspath( os.path.dirname(sys.executable) )
    else:
        path = os.path.abspath( os.path.dirname(__file__) )
        path = os.path.split(path)[0]
    return os.path.join(path, 'visvisResources')


def getAppDataDirDir():
    """ getAppDataDirDir()
    
    Get the directory where visvis can store user-specific data.
    
    """
    # Define user dir and appDataDir
    userDir = os.path.expanduser('~')    
    appDataDir = os.path.join(userDir, '.visvis')
    if sys.platform.startswith('win') and 'APPDATA' in os.environ:
        appDataDir = os.path.join( os.environ['APPDATA'], 'visvis' )
    
    # Make sure it exists
    if not os.path.isdir(appDataDir):
        os.mkdir(appDataDir)
    
    return appDataDir
    



class Settings(object):
    def __init__(self):
        
        # Define settings file name
        self._fname = os.path.join(getAppDataDirDir(), 'config.ssdf')
        
        # Load settings if we can
        s = ssdf.new()
        if os.path.exists(self._fname):
            try:
                s = ssdf.load(self._fname)
            except Exception:
                pass
        
        # Store
        self._s = s
        
        # todo: load any default values ans save back in __init__
        # todo: use the settings in all parts where it applies
            
    def _Save(self):
        ssdf.save(self._fname, self._s)
    
    @Property
    def preferredBackend():
        def fget(self):
            if 'backend' in self._s:
                return self._s.backend
            else:
                return 'qt4'
        def fset(self, value):
            value = value.lower()
            if value in ['qt4', 'wx', 'gtk', 'fltk']:
                self._s.backend = value
            else:
                raise ValueError('Invalid backend specified.')
            self._Save()
    

# Create settings instance    
settings = Settings()

# Set __file__ absolute when loading
__file__ = os.path.abspath(__file__)
