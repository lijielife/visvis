# -*- coding: utf-8 -*-
# Copyright (c) 2010, Almar Klein
#
# Visvis is distributed under the terms of the (new) BSD License.
# The full license can be found in 'license.txt'.

""" Module sliders

Implements a few slider widgets.

"""

import OpenGL.GL as gl

from visvis.pypoints import Pointset, Point
from visvis.core.events import BaseEvent
from visvis.core.misc import PropWithDraw, Range
from visvis.core.axises import GetTicks
from visvis import Box, Label


class BaseSlider(Box):
    """ BaseSlider(parent)
    
    Abstract slider class forming the base for the
    Slider and RangeSlider classes.
    
    """
    
    def __init__(self, parent):
        Box.__init__(self, parent)
        
        # init size
        self.position.w = 300
        self.position.h = 40
        
        # Slider specific stuff
        self._fullRange = Range(0,1)
        self._range = Range(0,1)
        self._refRange = Range(0,1) # For sliding
        self._showTicks = False
        
        # Set bgcolor and edge
        self.bgcolor = (0.6, 0.8, 0.6)
        self._frontColor = 0.5, 0.7, 0.9
        self.edgeWidth = 1
        
        # A slider should respond to mouse
        self.hitTest = True
        
        # Create label centered at the box
        self._label = Label(self)
        self._label.position = 0,0,1,1
        self._label.halign = 0
        self._label.bgcolor = None
        
        # State variables
        self._isOver = False
        self._sliderDown = False
        self._sliderRefx = 0.0
        
        # Pool of labels for tickmarks, to reuse them
        self._wobjects = [] # So we can have Text objects
        self._labelPool = {}
        
        # Calculate dots now
        self._SliderCalcDots()
        
        # Create new events
        self._eventSliding = BaseEvent(self)
        self._eventSliderChanged = BaseEvent(self)
        
        # To changes appearance on mouse over
        self.eventEnter.Bind(self._SliderOnEnter)
        self.eventLeave.Bind(self._SliderOnLeave)
        
        # Bind to events
        self.eventMouseDown.Bind(self._SliderOnDown)
        self.eventMouseUp.Bind(self._SliderOnUp)
        self.eventMotion.Bind(self._SliderOnMotion)
        self.eventPosition.Bind(self._SliderCalcDots)
    
    
    @property
    def eventSliding(self):
        """ Event fired when the user is sliding the slider. This can
        occur manu times during one sliding-opertaion.
        """
        return self._eventSliding
    
    
    @property    
    def eventSliderChanged(self):
        """ Event fired when the user releases the moude while changing
        the slider.
        """
        return self._eventSliderChanged
    
    
    @PropWithDraw
    def fullRange():
        """ The full possible range for this slider.
        """
        def fget(self):
            return self._fullRange
        def fset(self, value):
            self._fullRange = Range(value)
            self._limitRangeAndSetText()
    
    @PropWithDraw
    def showTicks():
        """ Whether to show tickmarks (default False).
        """
        def fget(self):
            return self._showTicks
        def fset(self, value):
            self._showTicks = bool(value)
    
    
    def _SliderOnEnter(self, event):
        self._isOver = True
        self.Draw()
    
    
    def _SliderOnLeave(self, event):
        self._isOver = False
        self.Draw()
    
    
    def _SliderOnDown(self, event):
        
        # Calc positions in normalized units
        x0 = self._getNormalizedCurrentPos(event)
        x1, x2 = self._getNormalizedSliderLimits()
        
        # Determine offset
        w,h = self.position.size
        offset = 8.0 / max(w,h)
        
        if x0 < x1+offset:
            # Move on left edge
            self._sliderDown = 1 
            self._sliderRefx = x1 - x0
        elif x0 > x2-offset:
            # Move on right edge
            self._sliderDown = 3
            self._sliderRefx = x2 - x0
        else:
            self._sliderDown = 2 # Move middle
            self._sliderRefx = (x1+x2)/2.0 - x0
        
        # Store original
        self._refRange = Range(self._range)
        
        # Update
        self.Draw()
    
    
    def _SliderOnMotion(self, event):
        
        if not self._sliderDown:
            return 
        
        # Calc current position in normalized units
        x0 = self._getNormalizedCurrentPos(event)
        
        # Reset before updating
        self._range = Range(self._refRange)
        
        # New normalized position
        dx =  x0 + self._sliderRefx
        offset = self._fullRange.min
        
        if self._sliderDown == 1:
            # Move on left edge
            self._range.min = self._fullRange.range * dx + offset
        elif self._sliderDown == 3:
            # Move on right edge
            self._range.max = self._fullRange.range * dx + offset
        elif self._sliderDown == 2:
            # Move whole slider
            ra2 = self._refRange.range / 2.0 
            mi = self._fullRange.range * dx - ra2 + offset
            ma = self._fullRange.range * dx + ra2 + offset
            self._range.Set(mi,ma)
        
        # Limit and update
        self._limitRangeAndSetText()
        self._eventSliding.Set()
        self._eventSliding.Fire()
        self.Draw()
    
    def _SliderOnUp(self, event):
        
        # Update values
        self._SliderOnMotion(event)
        
        # Release
        self._sliderDown = 0
        
        # Update
        self._eventSliderChanged.Set()
        self._eventSliderChanged.Fire()
    
    
    def _limitRangeAndSetText(self):
        """ _limitRangeAndSetText()
        To limit the range of the slider and to set the slider text.
        Different slider implementation want to do this
        differently.
        """
        pass # Abstact method
    
    
    def _getNormalizedCurrentPos(self, event):
        """ _getNormalizedCurrentPos(event)
        Get the current mouse position as a normalized range unit
        (between 0 and 1, with the fullRange as a references).
        """
        w,h = self.position.size
        if w > h:            
            return float(event.x) / self.position.width
        else:
            return float(event.y) / self.position.height
    
    
    def _getNormalizedSliderLimits(self):
        """ _getNormalizedSliderLimits()
        Get the current limits of the slider expressed in normalized 
        units (between 0 and 1, with the fullRange as a references).
        """
        # Short names
        R1 = self._range
        R2 = self._fullRange
        #
        factor = R2.range        
        x1 = (R1.min - R2.min) / factor
        x2 = x1 + R1.range / factor
        #
        return x1, x2
    
    
    def _GetBgcolorToDraw(self):
        """ Can be overloaded to indicate mouse over in buttons. 
        """
        clr = list(self._bgcolor)
        if self._isOver:
            clr = [c+0.05 for c in clr]
        return clr
    
    
    def _getformat(self):
        """ Get the format in which to display the slider limits. 
        """
        if self._fullRange.range > 10000:
            return '%1.4g'
        elif self._fullRange.range > 1000:
            return '%1.0f'
        elif self._fullRange.range > 100:
            return '%1.1f'
        elif self._fullRange.range > 10:
            return '%1.2f'
        else:
            return '%1.4g'
    
    
    def _SliderCalcDots(self, event=None):
        
        # Init dots
        dots1, dots2 = Pointset(2), Pointset(2)
        
        # Get width height
        w,h = self.position.size
        
        # Fill pointsets
        if w > h:
            i = 5
            while i < h-5:
                dots1.append(2,i); dots1.append(5,i)
                dots2.append(-2,i); dots2.append(-5,i)
                i += 3
        else:
            i = 5
            while i < w-5:
                dots1.append(i,2); dots1.append(i,5)
                dots2.append(i,-2); dots2.append(i,-5)
                i += 3
        
        self._dots1, self._dots2 = dots1, dots2
    
    
    def OnDraw(self):
        
        # Draw bg color and edges
        Box.OnDraw(self)
        
        # Margin
        d1 = 2
        d2 = d1+1
        
        # Get normalize limits        
        t1, t2 = self._getNormalizedSliderLimits()
        
        # Get widget shape
        w, h = self.position.size
        
        # Calculate real dimensions of patch
        if w > h:
            x1, x2 = max(d2, t1*w), min(w-d1, t2*w)            
            y1, y2 = d1, h-d2
            #
            dots1 = self._dots1 + Point(x1, 0)
            dots2 = self._dots2 + Point(x2, 0)
            #
            diff = abs(x1-x2)
            #
            self._label.textAngle = 0
        else:            
            x1, x2 = d2, w-d1
            y1, y2 = max(d1, t1*h), min(h-d2, t2*h)
            #
            dots1 = self._dots1 + Point(0, y1)
            dots2 = self._dots2 + Point(0, y2)
            #
            diff = abs(y1-y2)
            #
            self._label.textAngle = -90
        
        # Draw slider bit
        clr = self._frontColor
        gl.glColor(clr[0], clr[1], clr[2], 1.0)            
        #
        gl.glBegin(gl.GL_POLYGON)
        gl.glVertex2f(x1,y1)
        gl.glVertex2f(x1,y2)
        gl.glVertex2f(x2,y2)
        gl.glVertex2f(x2,y1)
        gl.glEnd()
        
        
        # Draw dots
        if True:
            
            # Prepare
            gl.glColor(0,0,0,1)
            gl.glPointSize(1)
            gl.glDisable(gl.GL_POINT_SMOOTH)
            
            # Draw
            gl.glEnableClientState(gl.GL_VERTEX_ARRAY)
            if isinstance(self, RangeSlider) and diff>5:
                gl.glVertexPointerf(dots1.data)
                gl.glDrawArrays(gl.GL_POINTS, 0, len(dots1))
            if diff>5:
                gl.glVertexPointerf(dots2.data)
                gl.glDrawArrays(gl.GL_POINTS, 0, len(dots2))
            gl.glDisableClientState(gl.GL_VERTEX_ARRAY)
        
        
        if self._showTicks:
            
            # Reset color to black
            gl.glColor(0,0,0,1)
            
            # Draw ticks
            if w>h:
                p0 = Point(0, h)
                p1 = Point(w, h)
                delta = Point(0,3)
                halign, valign = 0, 0
                xoffset, yoffset = -8, -2
            else:
                p0 = Point(w, h)
                p1 = Point(w, 0)
                delta = Point(3,0)
                halign, valign = -1, 0
                xoffset, yoffset = 5, -8
            
            # Get tickmarks
            ticks, ticksPos, ticksText = GetTicks(p0, p1, self._fullRange)
            
            newLabelPool = {}
            linePieces = Pointset(2)
            for tick, pos, text in zip(ticks, ticksPos, ticksText):
                pos2 = pos + delta
                
                # Add line piece
                linePieces.append(pos); linePieces.append(pos2)
                
                # Create or reuse label
                if tick in self._labelPool:
                    label = self._labelPool.pop(tick)
                else:
                    label = Label(self, ' '+text+' ')
                    label.bgcolor = ''
                
                # Position label and set text alignment
                newLabelPool[tick] = label
                label.halign, label.valign = halign, valign
                label.position.x = pos2.x + xoffset
                label.position.w = 16
                label.position.y = pos2.y + yoffset
            
            # Clean up label pool
            for label in self._labelPool.values():
                label.Destroy()
            self._labelPool = newLabelPool
            
            # Draw line pieces
            gl.glLineWidth(1)
            gl.glEnableClientState(gl.GL_VERTEX_ARRAY)
            gl.glVertexPointerf(linePieces.data)
            gl.glDrawArrays(gl.GL_LINES, 0, len(linePieces))
            gl.glDisableClientState(gl.GL_VERTEX_ARRAY)
        

class Slider(BaseSlider):
    """ Slider(parent, fullRange=(0,1), value=0.5)
    
    A slider with which a scalar value can be interactively changed.
    The slider can be horizontal or vertical, depending on its 
    width/height ratio.
    
    """
    
    def __init__(self, parent, fullRange=(0,1), value=0.5):
        BaseSlider.__init__(self, parent)
        
        self.fullRange = fullRange
        self.value = value
    
    @PropWithDraw
    def value():
        """ The current value for this slider. 
        """
        def fget(self):
            return self._range.max
        def fset(self, value):
            self._range.max = float(value)
            self._limitRangeAndSetText()
            #
            self._eventSliderChanged.Set()
            self._eventSliderChanged.Fire()
    
    def _limitRangeAndSetText(self):
        # Limit
        self._range.max = min(self._range.max, self._fullRange.max)
        self._range.max = max(self._range.max, self._fullRange.min)
        self._range.min = self._fullRange.min
        
        # Set text
        tmp = self._getformat()
        self._label.text = tmp % self._range.max


class RangeSlider(BaseSlider):
    """ RangeSlider(parent, fullRange=(0,1), range=(0.25,0.75))
    
    A slider with which two scalar values (representing a range)
    can be interactively changed. The slider can be horizontal or 
    vertical, depending on its width/height ratio.
    
    """
    
    def __init__(self, parent, fullRange=(0,1), range=(0.25,0.75)):
        BaseSlider.__init__(self, parent)
        
        self.fullRange = fullRange
        self.range = range
    
    
    @PropWithDraw
    def range():
        """ The current range for this slider. 
        """
        def fget(self):
            return self._range
        def fset(self, value):
            self._range = Range(value)
            self._limitRangeAndSetText()
            #
            self._eventSliderChanged.Set()
            self._eventSliderChanged.Fire()
    
    def _limitRangeAndSetText(self):
        # Limit
        self._range.max = min(self._range.max, self._fullRange.max)
        self._range.max = max(self._range.max, self._fullRange.min)
        #
        self._range.min = max(self._range.min, self._fullRange.min)
        self._range.min = min(self._range.min, self._fullRange.max)
        
        # Set text
        tmp = self._getformat()
        tmp = tmp + u'  \u2013  ' + tmp
        self._label.text = tmp % (self._range.min, self._range.max)
