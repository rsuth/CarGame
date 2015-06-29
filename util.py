from __future__ import division
import math

def ease_in(a, b, percent):
    return a + (b-a) * math.pow(percent, 2)

def ease_out(a, b, percent):
    return a + (b-a) * (1 - math.pow((1 - percent), 2))

def ease_in_out(a, b, percent):
    return a + (b-a) * (((-1 * math.cos(percent*math.pi))/2) + 0.5)

def percent_remaining(n, total):
    return (n % total)/total
