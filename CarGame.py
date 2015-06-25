from __future__ import division
import pygame, sys, os
import math
from pygame.locals import *

# colors:
LIGHT = {'road': (143, 143, 143), 'grass': (54, 209, 46),
    'rumble': (237, 237,237), 'lanemarker': (143, 143, 143)}
DARK = {'road': (138, 138, 138), 'grass': (51, 184, 44),
    'rumble': (240, 81, 103), 'lanemarker': (237, 237,237)}

# configuration constants
SCREEN_W = 640
SCREEN_H = 400
FPS = 30
DRAW_DISTANCE = 200
CAMERA_HEIGHT = 1000
CAMERA_DEPTH = .8
SEGMENT_LENGTH = 140
RUMBLE_LENGTH = 3
ROAD_WIDTH = 1800
MAX_SPEED = 300

def load_image(name, colorkey=None):
    fullname = os.path.join('data', name)
    try:
        image = pygame.image.load(fullname)
    except pygame.error, message:
        print 'Cannot load image:', name
        raise SystemExit, message
    image = image.convert()
    return image

def initialize_window(w, h):
    pygame.init()
    screen = pygame.display.set_mode([w, h])
    return screen

def reset_road():
    segments = []
    for n in xrange(0,500): # 500 is road length, arbitrary
        segment = {'index': n,
                   'p1': {'world':  {'z':n * SEGMENT_LENGTH, 'x':0, 'y': 0 },
                          'camera': {'x': 0, 'y': 0, 'z': 0},
                          'screen': { 'x': 0, 'y': 0, 'scale': 0, 'w':0}
                          },
                   'p2': {'world':  {'z':(n+1) * SEGMENT_LENGTH, 'x':0, 'y':0},
                          'camera': { 'x': 0, 'y':0, 'z': 0},
                          'screen': { 'x': 0, 'y': 0, 'scale': 0, 'w':0}
                          },
                   'color': LIGHT if ( math.floor(n / RUMBLE_LENGTH) % 2 == 0) else DARK }
        segments.append(segment)
    return segments

def find_segment(z_value, segments):
    segment = int(math.floor(z_value/SEGMENT_LENGTH) % len(segments))
    return segments[segment]

def get_image_line(image, y, x):
    line = pygame.Surface((image.get_width,1))
    line.blit(image, (x, 0), (0,y,500,1))
    return line

def render_road(screen, segments, position, player_x):
    base_segment = find_segment(position, segments)
    max_y = SCREEN_H
    for n in xrange(0, DRAW_DISTANCE):
        segment = segments[(base_segment['index']+n)%len(segments)]
        segment_looped = segment['index'] < base_segment['index']

        project_point(segment['p1'], (player_x*ROAD_WIDTH), CAMERA_HEIGHT,
                        position - (track_length if segment_looped else 0),
                        CAMERA_DEPTH, SCREEN_W, SCREEN_H, ROAD_WIDTH)
        project_point(segment['p2'], (player_x*ROAD_WIDTH), CAMERA_HEIGHT,
                        position - (track_length if segment_looped else 0),
                        CAMERA_DEPTH, SCREEN_W, SCREEN_H, ROAD_WIDTH)
        if ((segment['p1']['camera']['z'] <= CAMERA_DEPTH)
            or (segment['p2']['camera']['y'] >= max_y)):
            continue
        render_segment(screen, segment)
        max_y = segment['p2']['screen']['y']

def render_segment(screen, segment):
    v1 = ((segment['p1']['screen']['x'] - segment['p1']['screen']['w']),
            segment['p1']['screen']['y'])
    v2 = ((segment['p1']['screen']['x'] + segment['p1']['screen']['w']), v1[1])
    v3 = ((segment['p2']['screen']['x'] + segment['p2']['screen']['w']),
            segment['p2']['screen']['y'])
    v4 = ((segment['p2']['screen']['x'] - segment['p2']['screen']['w']), v3[1])

    r1 = ((v1[0]-(segment['p1']['screen']['w']/6)), (v1[1]))
    r2 = ((v2[0]+(segment['p1']['screen']['w']/6)), (v2[1]))
    r3 = ((v3[0]+(segment['p2']['screen']['w']/6)), (v3[1]))
    r4 = ((v4[0]-(segment['p2']['screen']['w']/6)), (v4[1]))

    l1 = ((v1[0] + (segment['p1']['screen']['w']) - (segment['p1']['screen']['w']/50)), v1[1])
    l2 = ((v1[0] + (segment['p1']['screen']['w']) + (segment['p1']['screen']['w']/50)), v2[1])
    l3 = ((v4[0] + (segment['p2']['screen']['w']) + (segment['p2']['screen']['w']/50)), v3[1])
    l4 = ((v4[0] + (segment['p2']['screen']['w']) - (segment['p2']['screen']['w']/50)), v4[1])

    road_point_list = [v1, v2, v3, v4]
    rumble_point_list = [r1, r2, r3, r4]
    grass_rect = (0, v3[1], SCREEN_W, (v1[1]-v3[1]))
    lanemarker_point_list = [l1, l2, l3, l4]

    screen.fill(segment['color']['grass'], grass_rect)
    pygame.draw.polygon(screen, segment['color']['rumble'], rumble_point_list)
    pygame.draw.polygon(screen, segment['color']['road'], road_point_list)
    pygame.draw.polygon(screen, segment['color']['lanemarker'], lanemarker_point_list)

def project_point(pt_3d, cam_x, cam_y, cam_z, cam_depth, w, h, road_w):
    pt_3d['camera']['x'] = (pt_3d['world']['x'] or 0) - cam_x
    pt_3d['camera']['y'] = (pt_3d['world']['y'] or 0) - cam_y
    pt_3d['camera']['z'] = (pt_3d['world']['z'] or 0) - cam_z

    pt_3d['screen']['scale'] = cam_depth / (pt_3d['camera']['z'] or 1)

    pt_3d['screen']['x'] = int(round((w/2) +
        (pt_3d['screen']['scale'] * pt_3d['camera']['x'] * (w/2))))

    pt_3d['screen']['y'] = int(round((h/2) -
        (pt_3d['screen']['scale'] * pt_3d['camera']['y'] * (h/2))))

    pt_3d['screen']['w'] = int(round(pt_3d['screen']['scale']*road_w*(w/2)))

def handle_events():
    global gas
    global brake
    global steer_left
    global steer_right

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            pygame.quit()
            sys.exit()
        elif event.type == pygame.KEYDOWN:
            if event.key == K_UP:
                gas = True
            if event.key == K_DOWN:
                brake = True
            if event.key == K_LEFT:
                steer_left = True
            if event.key == K_RIGHT:
                steer_right = True
        elif event.type == pygame.KEYUP:
            if event.key == K_UP:
                gas = False
            if event.key == K_DOWN:
                brake = False
            if event.key == K_LEFT:
                steer_left = False
            if event.key == K_RIGHT:
                steer_right = False

Window = initialize_window(SCREEN_W, SCREEN_H)
clock = pygame.time.Clock()

#============================================================
#=====================GAME VARIABLES=========================
#============================================================
background = load_image("mountains.png")
road_segments = reset_road()
speed = 0
gas = False
brake = False
steer_left = False
steer_right = False
accel = 1
deccel = 1
player_x = 0
position = 0
steer = 0
track_length = len(road_segments) * SEGMENT_LENGTH

#============================================================
#=====================GAME LOOP==============================
#============================================================
while True:
    handle_events()
    if gas and speed < MAX_SPEED:
        speed += accel
    if not gas and speed > deccel:
        speed -= deccel
    if brake and speed > deccel*2:
        speed -= deccel*2
    if brake and speed <= deccel:
        speed = 0
    if steer_right:
        steer = .0002 * speed
    elif steer_left:
        steer = -.0002 * speed
    else:
        steer = 0

    position += speed
    player_x += steer

    # keep road from running out
    while position >= track_length:
        position -= track_length
    while position < 0:
        position += track_length

    Window.blit(background, [0,0])
    render_road(Window, road_segments, position, player_x)
    pygame.display.flip()
    clock.tick(FPS)
