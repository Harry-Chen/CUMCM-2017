#!/use/bin/env python3
# -*- coding: utf8 -*-

import matplotlib.pyplot as plt
import copy
import numpy as np
import scipy.stats
from sklearn import linear_model
import math
import re
import fileinput

def load_data(filename):
    f = open(filename, 'r').read()
    return [list(map(float, s.split('\t')))
            for s in f.replace(' ', '').strip().split('\n')]

attach_1 = load_data('attachment1.txt')
attach_2 = load_data('attachment2.txt')
attach_3 = load_data('attachment3.txt')
attach_5 = load_data('attachment5.txt')

# Question 1
data1 = np.array(attach_2)
data1 = np.transpose(data1)

# find the position of the circle in the first scanline
for i in range(511, 0, -1):
    if data1[0][i] != 0:
        circle_bottom = i
        break

for i in range(circle_bottom, 0, -1):
    if data1[0][i] == 0:
        circle_top = i + 1
        break

circle = [(circle_top, circle_bottom)]
circle_shift = 5

for i in range(1, 120):
    ct, cb = circle[-1]
    # find circle top
    max_now, max_id = -1, 999
    for shift in range(1, circle_shift):
        val = data1[i][ct - shift] - data1[i][ct - shift - 1]
        if val > max_now:
            max_id, max_now = ct - shift, val
    ct = min(max_id, ct)

    # find circle bottom
    max_now, max_id = -1, 999
    for shift in range(1, circle_shift):
        val = data1[i][cb - shift - 1] - data1[i][cb - shift]
        if val > max_now:
            max_id, max_now = cb - shift, val
    cb = min(max_id, cb)

    circle.append((ct, cb))

for i in range(120, 180):
    for j in range(0, 512):
        if data1[i][j] != 0:
            ct = j
            break
    for j in range(ct, 512):
        if data1[i][j] == 0:
            cb = j - 1
            break
    circle.append((ct, cb))

def find_bottom(data, start):
    for i in range(start, 0, -1):
        if data[i] != 0:
            return i

ellipse_shift = 5
ellipse_bottom = [find_bottom(data1[0], 390)]

for i in range(1, 30):
    eb = ellipse_bottom[-1]
    # find circle bottom
    max_now, max_id = -1, 0
    for shift in range(1, circle_shift):
        val = data1[i][eb + shift - 1] - data1[i][eb + shift]
        if val > max_now:
            max_id, max_now = eb + shift - 1, val
    ellipse_bottom.append(max(max_id, eb))

for i in range(30, 180):
    ellipse_bottom.append(find_bottom(data1[i], 511))

def find_top(data, start):
    for i in range(start, 512):
        if data[i] != 0:
            return i

ellipse_top = [find_top(data1[i], 0) for i in range(85)]

for i in range(85, 120):
    et = ellipse_top[-1]
    # find circle top
    max_now, max_id = -1, 0
    for shift in range(0, circle_shift):
        val = data1[i][et + shift] - data1[i][et + shift - 1]
        if val > max_now:
            max_id, max_now = et + shift, val
    ellipse_top.append(max(max_id, et))

ellipse_top.extend([find_top(data1[i], 120) for i in range(120, 180)])

# output to file
open('bound-circle.txt', 'w').write('\n'.join(
    [str(c[0]) + '\t' + str(c[1]) for c in circle]))
open('bound-ellipse.txt', 'w').write('\n'.join(
    [str(ellipse_top[i]) + '\t' + str(ellipse_bottom[i]) for i in range(180)]))

# scanline width
def get_circle_scanline(i):
    return data1[i][circle[i][0]:circle[i][1] + 1]

def scanline_width(line):
    n = len(line)
    y = [0.25 * (line[0] * line[0] - line[i] * line[i]) for i in range(1, n)]
    X = [(2 * i, i * i) for i in range(1, n)]
    clf = linear_model.LinearRegression()
    clf.fit(X, y)
    _, LL = clf.coef_
    return math.sqrt(LL)

l_i_many = [scanline_width(get_circle_scanline(i)) for i in range(110, 180)]
l_i = np.mean(l_i_many)

d_i_many = [max(get_circle_scanline(i)) for i in range(110, 180)] \
         + [max(get_circle_scanline(i)) for i in range(0, 14)]
d_i = max(d_i_many)
d_s = d_i / l_i  # circle radius in scanline

def find_bound_s(index, ignore=2):
    cb, ct = circle[index]
    line = data1[index]
    circle_line = line[cb : ct + 1]
    peak = np.argmax(circle_line)

    d_center_s = [0.5 * math.sqrt(d_i * d_i - l * l) / l_i for l in circle_line]

    center_many = []
    for i, dc_s in enumerate(d_center_s[: peak - ignore]):
        center_many.append(cb + i + dc_s)

    for i, dc_s in enumerate(d_center_s[peak + ignore + 1: ]):
        base = cb + i + peak + ignore + 1
        center_many.append(base - dc_s)

    center_s = np.mean(center_many)
 #   print(np.var(center_many))

    return center_s - 0.5 * d_s, center_s + 0.5 * d_s

bound_0_13 = [find_bound_s(i) for i in range(13)]
bound_110_180 = [find_bound_s(i) for i in range(110, 180)]

def get_angle(width):
    D = d * width
    s = 2880/11 * (1/225 - 4/(D**2))
    t = math.asin(s)
    n2 = math.atan(math.sqrt((4*40*40-D**2)/(D**2-4*15*15)))
    return n2 * 180 / math.pi

open('middle_0_13.txt', 'w').write('\n'.join([str(0.5 * (y + x)) for x, y in bound_0_13]))
open('middle_110_180.txt', 'w').write('\n'.join([str(0.5 * (y + x)) for x, y in bound_110_180]))

def extract_ellipse(index, ignore=3):
    et, eb = ellipse_top[index] + ignore, ellipse_bottom[index] - ignore
    ct, cb = circle[index]
    ct, cb = ct - ignore, cb + ignore

    line = data1[index]
    scan_lines = []
    for e in range(et, eb):
        if ct <= e <= cb or not line[e]:
            continue
        scan_lines.append((e - et, line[e]))
    return scan_lines

ellipse_slines = [extract_ellipse(i) for i in range(180)]

def write_ellipse_to_file(filename, line_id):
    f = open(filename, 'w')
    f.write('\n'.join(str(n) + ' ' + str(L) for n, L in ellipse_slines[line_id]))
    f.close()

for i in range(180):
    write_ellipse_to_file('ellipse_scanline/%d.txt' % i, i)

# waiting for Mathematica's output
input('Waiting for Mathematica\' Output')

def load_angle_data(filename):
    slope_many = []
    for line in open(filename, 'r').read().split('\n'):
        if line.strip():
            slope_one_many = re.findall(r'\{-?\d*\.?\d*, (-?\d*\.?\d*)\}', line)
            slope_many.append(abs(float(slope_one_many[0])))
    return slope_many

def calc_angle(index):
    if 138 <= index <= 161:
        is_inverted = True
        filename = 'ellipse_scanline/ans_inverted_step_1/%d.txt'
    else:
        is_inverted = False
        filename = 'ellipse_scanline/ans_step_1/%d.txt'
    slope_many = load_angle_data(filename % index)
    if not slope_many: return 0
    slope = np.mean(slope_many)
    omega = math.pi / 2 - math.atan(slope) if is_inverted else math.atan(slope)
    if index <= 60: theta = math.pi / 2 - omega
    elif index <= 150: theta = math.pi / 2 + omega
    else: theta = 3 * math.pi / 2 - omega
    return theta, np.std(np.arctan(slope_many))

angles = [ calc_angle(i)[0] * 180 / math.pi for i in range(180) ]

angle_f = open('angle_middle_0_13.txt', 'w')
angle_f.write('\n'.join([str(angles[i]) + ' ' + str((bound_0_13[i][1] + bound_0_13[i][0] - 511) / 2) for i in range(13)]))
angle_f.close()
angle_f = open('angle_middle_110_180.txt', 'w')
angle_f.write('\n'.join([str(angles[i]) + ' ' + str((bound_110_180[i - 110][1] + bound_110_180[i - 110][0] - 511) / 2) for i in range(110, 180)]))
angle_f.close()

# Waiting for Mathematica's Output
input('Waiting for Mathematica\' Output')

def load_center_data(filename):
    data = open(filename, 'r').read()
    center_many = re.findall(r'\{(-?\d*\.?\d*), (-?\d*\.?\d*)\}', data)
    center_many = [ list(map(float, line)) for line in center_many ]
    return center_many

center_offset_many_s = load_center_data('center_coords.txt')
center_offset_s = np.mean(center_offset_many_s, axis=0)
center_mm = [45, 0] - 8 / d_s * center_offset_s

# Question 2
d_mm = 8      # diameter of circle in mm
scale_i2mm = d_mm / d_i
scale_mm2p = 256 / 100.
scale_i2p  = scale_i2mm * scale_mm2p

proj_axis_s = np.array(range(512)) - 0.5 * 511
proj_axis_p = proj_axis_s * l_i * scale_i2p

center_p = center_mm * scale_mm2p
thetas = np.array(angles) * math.pi / 180

def proj_pixel_dist(pixel, theta, center_p):
    p_x = pixel[0] - center_p[0]
    p_y = pixel[1] - center_p[1]
    return p_x * np.cos(theta) + p_y * np.sin(theta)

def proj_direct(g, axis_p, theta, center_p):
    size = 256
    mu = np.zeros([size, size])
    for n in range(len(theta)):
        R_flatten = [ proj_pixel_dist([x - (size - 1) / 2, y - (size - 1) / 2], theta[n], center_p)
                     for x in range(size) for y in range(size) ]
        g_theta = np.reshape(np.interp(R_flatten, axis_p, g[n]), [size, size])
        mu = mu + g_theta
    return np.flip(np.transpose(mu), axis=0)

# Filtering
def filter_projection(g, H):
    return np.real(np.fft.ifft(np.fft.fft(g, axis=1) * H, axis=1))

def RL_conv(rho_0, length):
    T = 0.5 / rho_0
    h = []
    for i in range(0, length // 2 + 1):
        if i == 0:
            h.append(0.25 / T ** 2)
        elif i % 2 == 0:
            h.append(0)
        else:
            h.append(-1. / (math.pi * i * T) ** 2)
    h += list(reversed(h[1:-1]))
    return np.real(np.fft.fft(h))

def get_kernel():
    return RL_conv(0.5 / (l_i * scale_i2p), 512)

def inv_proj(data, kernel=None):
    if kernel is None: kernel = get_kernel()
    return proj_direct(filter_projection(np.transpose(data), kernel), proj_axis_p, thetas, center_p)

def filter_min0(data):
    for i in range(256):
        for j in range(256):
            data[i][j] = max(data[i][j], 0)
    return data

# Generating Data
attach2_recons = filter_min0(inv_proj(attach_2))
attach3_recons = filter_min0(inv_proj(attach_3))
attach5_recons = filter_min0(inv_proj(attach_5))

# Recons Intensity
max_attach2_recons = np.max(np.abs(attach2_recons))
scale_recons = 1.0 / np.mean([ x for x in np.reshape(np.abs(attach2_recons), [256 * 256]) if x > max_attach2_recons * 0.5 ])

attach_4 = load_data('attachment4.txt')
pixels = np.array(attach_4) * scale_mm2p
pixels_x, pixels_y = zip(*pixels)

def compute_recons_intensity(data, pixels):
    g = filter_projection(np.transpose(data), get_kernel())
    mu = np.zeros(len(pixels))
    for n in range(len(thetas)):
        R = [ proj_pixel_dist(pixel, thetas[n], center_p) for pixel in pixels - (256 - 1) / 2 ]
        g_theta = np.interp(R, proj_axis_p, g[n])
        mu = mu + g_theta
    for i in range(len(pixels)):
        mu[i] = max(mu[i], 0)
    return mu * scale_recons

def compute_approx_intensity(data, pixels):
    return np.array([ data[255 - int(p[1])][int(p[0])] for p in pixels ]) * scale_recons

compute_recons_intensity(attach_2, pixels)
compute_recons_intensity(attach_3, pixels)
compute_recons_intensity(attach_5, pixels)

open('attach5_recons.txt', 'w').write('\n'.join([','.join(['%.4f' % attach5_recons[i][j] for j in range(256)]) for i in range(256)]))
open('attach3_recons.txt', 'w').write('\n'.join([','.join(['%.4f' % attach3_recons[i][j] for j in range(256)]) for i in range(256)]))
open('attach2_recons.txt', 'w').write('\n'.join([','.join(['%.4f' % attach2_recons[i][j] for j in range(256)]) for i in range(256)]))
open('angles.txt', 'w').write('\n' .join(['%.4f' % angle for angle in angles]))
