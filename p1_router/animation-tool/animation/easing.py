#!/usr/bin/env python3

"""
Easing Functions
Provides a collection of easing functions for animation interpolation.
"""

import math
from typing import Callable, Dict


class EasingFunctions:
    """
    Collection of easing functions for animation interpolation.
    
    All functions take a value t in the range [0.0, 1.0] and return
    a transformed value in the range [0.0, 1.0].
    """
    
    @staticmethod
    def linear(t: float) -> float:
        """Linear interpolation (no easing)."""
        return t
    
    @staticmethod
    def ease_in_quad(t: float) -> float:
        """Quadratic ease-in: t^2"""
        return t * t
    
    @staticmethod
    def ease_out_quad(t: float) -> float:
        """Quadratic ease-out: -t*(t-2)"""
        return -t * (t - 2)
    
    @staticmethod
    def ease_in_out_quad(t: float) -> float:
        """Quadratic ease-in-out."""
        t *= 2
        if t < 1:
            return 0.5 * t * t
        t -= 1
        return -0.5 * (t * (t - 2) - 1)
    
    @staticmethod
    def ease_in_cubic(t: float) -> float:
        """Cubic ease-in: t^3"""
        return t * t * t
    
    @staticmethod
    def ease_out_cubic(t: float) -> float:
        """Cubic ease-out: (t-1)^3 + 1"""
        t -= 1
        return t * t * t + 1
    
    @staticmethod
    def ease_in_out_cubic(t: float) -> float:
        """Cubic ease-in-out."""
        t *= 2
        if t < 1:
            return 0.5 * t * t * t
        t -= 2
        return 0.5 * (t * t * t + 2)
    
    @staticmethod
    def ease_in_sine(t: float) -> float:
        """Sinusoidal ease-in."""
        return -math.cos(t * (math.pi / 2)) + 1
    
    @staticmethod
    def ease_out_sine(t: float) -> float:
        """Sinusoidal ease-out."""
        return math.sin(t * (math.pi / 2))
    
    @staticmethod
    def ease_in_out_sine(t: float) -> float:
        """Sinusoidal ease-in-out."""
        return -0.5 * (math.cos(math.pi * t) - 1)
    
    @staticmethod
    def ease_in_expo(t: float) -> float:
        """Exponential ease-in."""
        return 0 if t == 0 else math.pow(2, 10 * (t - 1))
    
    @staticmethod
    def ease_out_expo(t: float) -> float:
        """Exponential ease-out."""
        return 1 if t == 1 else 1 - math.pow(2, -10 * t)
    
    @staticmethod
    def ease_in_out_expo(t: float) -> float:
        """Exponential ease-in-out."""
        if t == 0:
            return 0
        if t == 1:
            return 1
        t *= 2
        if t < 1:
            return 0.5 * math.pow(2, 10 * (t - 1))
        t -= 1
        return 0.5 * (-math.pow(2, -10 * t) + 2)
    
    @staticmethod
    def ease_in_elastic(t: float) -> float:
        """Elastic ease-in."""
        if t == 0:
            return 0
        if t == 1:
            return 1
        p = 0.3
        s = p / 4
        t -= 1
        return -(math.pow(2, 10 * t) * math.sin((t - s) * (2 * math.pi) / p))
    
    @staticmethod
    def ease_out_elastic(t: float) -> float:
        """Elastic ease-out."""
        if t == 0:
            return 0
        if t == 1:
            return 1
        p = 0.3
        s = p / 4
        return math.pow(2, -10 * t) * math.sin((t - s) * (2 * math.pi) / p) + 1
    
    @staticmethod
    def ease_in_out_elastic(t: float) -> float:
        """Elastic ease-in-out."""
        if t == 0:
            return 0
        if t == 1:
            return 1
        p = 0.3 * 1.5
        s = p / 4
        t *= 2
        if t < 1:
            t -= 1
            return -0.5 * (math.pow(2, 10 * t) * math.sin((t - s) * (2 * math.pi) / p))
        t -= 1
        return 0.5 * math.pow(2, -10 * t) * math.sin((t - s) * (2 * math.pi) / p) + 1
    
    @staticmethod
    def ease_in_back(t: float) -> float:
        """Back ease-in: overshooting cubic easing."""
        s = 1.70158
        return t * t * ((s + 1) * t - s)
    
    @staticmethod
    def ease_out_back(t: float) -> float:
        """Back ease-out: overshooting cubic easing."""
        s = 1.70158
        t -= 1
        return t * t * ((s + 1) * t + s) + 1
    
    @staticmethod
    def ease_in_out_back(t: float) -> float:
        """Back ease-in-out: overshooting cubic easing."""
        s = 1.70158 * 1.525
        t *= 2
        if t < 1:
            return 0.5 * (t * t * ((s + 1) * t - s))
        t -= 2
        return 0.5 * (t * t * ((s + 1) * t + s) + 2)
    
    @staticmethod
    def ease_in_bounce(t: float) -> float:
        """Bounce ease-in."""
        return 1 - EasingFunctions.ease_out_bounce(1 - t)
    
    @staticmethod
    def ease_out_bounce(t: float) -> float:
        """Bounce ease-out."""
        if t < (1 / 2.75):
            return 7.5625 * t * t
        elif t < (2 / 2.75):
            t -= (1.5 / 2.75)
            return 7.5625 * t * t + 0.75
        elif t < (2.5 / 2.75):
            t -= (2.25 / 2.75)
            return 7.5625 * t * t + 0.9375
        else:
            t -= (2.625 / 2.75)
            return 7.5625 * t * t + 0.984375
    
    @staticmethod
    def ease_in_out_bounce(t: float) -> float:
        """Bounce ease-in-out."""
        if t < 0.5:
            return EasingFunctions.ease_in_bounce(t * 2) * 0.5
        return EasingFunctions.ease_out_bounce(t * 2 - 1) * 0.5 + 0.5


# Create a dictionary mapping easing names to functions for easy lookup
EASING_FUNCTIONS: Dict[str, Callable[[float], float]] = {
    "linear": EasingFunctions.linear,
    "ease_in_quad": EasingFunctions.ease_in_quad,
    "ease_out_quad": EasingFunctions.ease_out_quad,
    "ease_in_out_quad": EasingFunctions.ease_in_out_quad,
    "ease_in_cubic": EasingFunctions.ease_in_cubic,
    "ease_out_cubic": EasingFunctions.ease_out_cubic,
    "ease_in_out_cubic": EasingFunctions.ease_in_out_cubic,
    "ease_in_sine": EasingFunctions.ease_in_sine,
    "ease_out_sine": EasingFunctions.ease_out_sine,
    "ease_in_out_sine": EasingFunctions.ease_in_out_sine,
    "ease_in_expo": EasingFunctions.ease_in_expo,
    "ease_out_expo": EasingFunctions.ease_out_expo,
    "ease_in_out_expo": EasingFunctions.ease_in_out_expo,
    "ease_in_elastic": EasingFunctions.ease_in_elastic,
    "ease_out_elastic": EasingFunctions.ease_out_elastic,
    "ease_in_out_elastic": EasingFunctions.ease_in_out_elastic,
    "ease_in_back": EasingFunctions.ease_in_back,
    "ease_out_back": EasingFunctions.ease_out_back,
    "ease_in_out_back": EasingFunctions.ease_in_out_back,
    "ease_in_bounce": EasingFunctions.ease_in_bounce,
    "ease_out_bounce": EasingFunctions.ease_out_bounce,
    "ease_in_out_bounce": EasingFunctions.ease_in_out_bounce,
}

# List of easing function names for UI display
EASING_NAMES = list(EASING_FUNCTIONS.keys()) 