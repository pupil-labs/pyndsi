'''
(*)~----------------------------------------------------------------------------------
 Pupil - eye tracking platform
 Copyright (C) 2012-2016  Pupil Labs

 Distributed under the terms of the GNU Lesser General Public License (LGPL v3.0).
 License details are in the file license.txt, distributed as part of this software.
----------------------------------------------------------------------------------~(*)

pyglui code taken from:
https://github.com/pupil-labs/pyglui/blob/master/example/example.py
'''

quit = False
import logging, time, signal, sys
logging.basicConfig(
    format='%(asctime)s [%(levelname)8s | %(name)-14s] %(message)s',
    datefmt='%H:%M:%S',
    level=logging.DEBUG
)
logger = logging.getLogger(__name__)
logger.setLevel(logging.WARNING)
logging.getLogger('ndsi').setLevel(logging.DEBUG)
logging.getLogger('pyre').setLevel(logging.WARNING)

import ndsi
import pprint, random

from glfw import *
from OpenGL.GL import *

import numpy as np

import time
from pyglui import __version__ as pyglui_version
#assert pyglui_version >= '2.0'

from pyglui import ui
from pyglui.cygl.utils import init
from pyglui.cygl.utils import RGBA
from pyglui.cygl.utils import draw_concentric_circles
from pyglui.pyfontstash import fontstash as fs
from pyglui.cygl.shader import Shader


width, height = (1280,720)

def basic_gl_setup():
    glEnable(GL_POINT_SPRITE )
    glEnable(GL_VERTEX_PROGRAM_POINT_SIZE) # overwrite pointsize
    glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
    glEnable(GL_BLEND)
    glClearColor(.8,.8,.8,1.)
    glEnable(GL_LINE_SMOOTH)
    # glEnable(GL_POINT_SMOOTH)
    glHint(GL_LINE_SMOOTH_HINT, GL_NICEST)
    glEnable(GL_LINE_SMOOTH)
    glEnable(GL_POLYGON_SMOOTH)
    glHint(GL_POLYGON_SMOOTH_HINT, GL_NICEST)


def adjust_gl_view(w,h,window):
    """
    adjust view onto our scene.
    """

    glViewport(0, 0, w, h)
    glMatrixMode(GL_PROJECTION)
    glLoadIdentity()
    glOrtho(0, w, h, 0, -1, 1)
    glMatrixMode(GL_MODELVIEW)
    glLoadIdentity()



def clear_gl_screen():
    glClearColor(.9,.9,0.9,1.)
    glClear(GL_COLOR_BUFFER_BIT)


class SensorUIWrapper(object):
    def __init__(self, gui, network, sensor_uuid):
        self._initial_refresh = True
        self.control_id_ui_mapping = {}
        self.gui = gui
        self.sensor = network.sensor(sensor_uuid, callbacks=(self.on_notification,))
        self.init_gui()

    def cleanup(self):
        self.deinit_gui()
        self.sensor.unlink()
        self.sensor = None

    def init_gui(self):
        menu_width = 400
        menu_height = 500
        x = random.random()
        y = random.random()
        x = int(x*(width-menu_width))
        y = int(y*(height-menu_height))

        self.menu = ui.Scrolling_Menu(unicode(self.sensor),size=(menu_width,menu_height),pos=(x,y))
        self.uvc_menu = ui.Growing_Menu("UVC Controls")
        self.gui.append(self.menu)
        self.update_control_menu()

    def deinit_gui(self):
        if self.menu:
            self.gui.remove(self.menu)
            self.menu = None
            self.uvc_menu = None
            self.control_id_ui_mapping = None

    def on_notification(self, sensor, event):
        if self._initial_refresh:
            self.sensor.refresh_controls()
            self._initial_refresh = False
        if event['subject'] == 'error':
            logger.error('Received error %i: %s'%(event['error_no'],event['error_str']))
        else:
            logger.info('%s [%s] %s %s'%(sensor, event['seq'], event['subject'], event['control_id']))
            logger.debug('SET %s'%event['changes'])
            ctrl_id = event['control_id']
            if event['changes'].get('value') is None:
                logger.warning('Control value for %s is None. This is not compliant with v2.12'%event['control_id'])
            ctrl_dtype = event.get('changes',{}).get('dtype')
            if (event['control_id'] not in self.control_id_ui_mapping or
                ctrl_dtype == "strmapping" or ctrl_dtype == "intmapping"):
                self.update_control_menu()

    def add_controls_to_menu(self,menu,controls):
        # closure factory
        def make_value_change_fn(ctrl_id):
            def initiate_value_change(val):
                logger.debug('%s: %s >> %s'%(self.sensor, ctrl_id, val))
                self.sensor.set_control_value(ctrl_id, val)
            return initiate_value_change

        for ctrl_id, ctrl_dict in controls:
            try:
                dtype    = ctrl_dict['dtype']
                ctrl_ui  = None
                if dtype == "string":
                    ctrl_ui = ui.Text_Input(
                        'value',
                        ctrl_dict,
                        label=ctrl_dict['caption'],
                        setter=make_value_change_fn(ctrl_id))
                elif dtype == "integer" or dtype == "float":
                    convert_fn = int if dtype == "integer" else float
                    ctrl_ui = ui.Slider(
                        'value',
                        ctrl_dict,
                        label=ctrl_dict['caption'],
                        min =convert_fn(ctrl_dict.get('min', 0)),
                        max =convert_fn(ctrl_dict.get('max', 100)),
                        step=convert_fn(ctrl_dict.get('res', 0.)),
                        setter=make_value_change_fn(ctrl_id))
                elif dtype == "bool":
                    ctrl_ui = ui.Switch(
                        'value',
                        ctrl_dict,
                        label=ctrl_dict['caption'],
                        on_val=ctrl_dict.get('max',True),
                        off_val=ctrl_dict.get('min',False),
                        setter=make_value_change_fn(ctrl_id))
                elif dtype == "strmapping" or dtype == "intmapping":
                    desc_list = ctrl_dict['map']
                    labels    = [desc['caption'] for desc in desc_list]
                    selection = [desc['value']   for desc in desc_list]
                    def make_selection_getter(ctrl_dict):
                        def getter():
                            mapping = ctrl_dict['map']
                            labels = [entry['caption'] for entry in mapping]
                            values = [entry['value']   for entry in mapping]
                            return values, labels
                        return getter
                    ctrl_ui = ui.Selector(
                        'value',
                        ctrl_dict,
                        label=ctrl_dict['caption'],
                        labels=labels,
                        selection=selection,
                        setter=make_value_change_fn(ctrl_id))
                else:
                    logger.warning('Unknown control type "%s"'%dtype)
                if ctrl_ui:
                    ctrl_ui.read_only = ctrl_dict.get('readonly',False)
                    self.control_id_ui_mapping[ctrl_id] = ctrl_ui
                    menu.append(ctrl_ui)
            except:
                logger.error('Exception for control:\n%s'%pprint.pformat(ctrl_dict))
                import traceback as tb
                tb.print_exc()
        if len(menu) == 0:
            menu.append(ui.Info_Text("No %s settings found"%menu.label))
        return menu

    def update_control_menu(self):
        del self.menu[:]
        del self.uvc_menu[:]
        self.control_id_ui_mapping = {}

        uvc_controls = []
        other_controls = []
        for entry in iter(sorted(self.sensor.controls.iteritems())):
            if entry[0].startswith("UVC"):
                uvc_controls.append(entry)
            else: other_controls.append(entry)

        self.add_controls_to_menu(self.menu, other_controls)
        self.add_controls_to_menu(self.uvc_menu, uvc_controls)
        self.menu.append(self.uvc_menu)

        self.menu.append(ui.Button("Reset to default values",self.sensor.reset_all_control_values))

def runNDSIClient():
    global quit
    quit = False

    # Callback functions
    def on_resize(window,w, h):
        h = max(h,1)
        w = max(w,1)
        hdpi_factor = glfwGetFramebufferSize(window)[0]/glfwGetWindowSize(window)[0]
        w,h = w*hdpi_factor,h*hdpi_factor
        gui.update_window(w,h)
        active_window = glfwGetCurrentContext()
        glfwMakeContextCurrent(window)
        # norm_size = normalize((w,h),glfwGetWindowSize(window))
        # fb_size = denormalize(norm_size,glfwGetFramebufferSize(window))
        adjust_gl_view(w,h,window)
        glfwMakeContextCurrent(active_window)


    def on_iconify(window,iconfied):
        pass

    def on_key(window, key, scancode, action, mods):
        gui.update_key(key,scancode,action,mods)

        if action == GLFW_PRESS:
            if key == GLFW_KEY_ESCAPE:
                on_close(window)
            if mods == GLFW_MOD_SUPER:
                if key == 67:
                    # copy value to system clipboard
                    # ideally copy what is in our text input area
                    test_val = "copied text input"
                    glfwSetClipboardString(window,test_val)
                    print "set clipboard to: %s" %(test_val)
                if key == 86:
                    # copy from system clipboard
                    clipboard = glfwGetClipboardString(window)
                    print "pasting from clipboard: %s" %(clipboard)


    def on_char(window,char):
        gui.update_char(char)

    def on_button(window,button, action, mods):
        # print "button: ", button
        # print "action: ", action
        gui.update_button(button,action,mods)
        # pos = normalize(pos,glfwGetWindowSize(window))
        # pos = denormalize(pos,(frame.img.shape[1],frame.img.shape[0]) ) # Position in img pixels

    def on_pos(window,x, y):
        hdpi_factor = float(glfwGetFramebufferSize(window)[0]/glfwGetWindowSize(window)[0])
        x,y = x*hdpi_factor,y*hdpi_factor
        gui.update_mouse(x,y)

    def on_scroll(window,x,y):
        gui.update_scroll(x,y)

    def on_close(window):
        global quit
        quit = True
        logger.info('Process closing from window')

    # get glfw started
    glfwInit()

    window = glfwCreateWindow(width, height, "pyglui demo", None, None)
    if not window:
        exit()

    glfwSetWindowPos(window,0,0)
    # Register callbacks for the window
    glfwSetWindowSizeCallback(window,on_resize)
    glfwSetWindowCloseCallback(window,on_close)
    glfwSetWindowIconifyCallback(window,on_iconify)
    glfwSetKeyCallback(window,on_key)
    glfwSetCharCallback(window,on_char)
    glfwSetMouseButtonCallback(window,on_button)
    glfwSetCursorPosCallback(window,on_pos)
    glfwSetScrollCallback(window,on_scroll)
    # test out new paste function

    glfwMakeContextCurrent(window)
    init()
    basic_gl_setup()

    print glGetString(GL_VERSION)


    class Temp(object):
        """Temp class to make objects"""
        def __init__(self):
            pass

    foo = Temp()
    foo.bar = 34
    foo.mytext = "some text"


    def set_text_val(val):
        foo.mytext = val
        # print 'setting to :',val


    print "pyglui version: %s" %(ui.__version__)

    gui = ui.UI()
    gui.scale = 1.0


    sensors = {}

    def on_network_event(network, event):
        if event['subject'] == 'attach':# and event['sensor_type'] == 'video':
            wrapper = SensorUIWrapper(gui,n,event['sensor_uuid'])
            sensors[event['sensor_uuid']] = wrapper
            logger.info('Linking sensor %s...'%wrapper.sensor)
            logger.debug('%s'%pprint.pformat(event))
        if event['subject'] == 'detach':# and event['sensor_type'] == 'video':
            logger.info('Unlinking sensor %s...'%event['sensor_uuid'])
            sensors[event['sensor_uuid']].cleanup()
            del sensors[event['sensor_uuid']]

    n = ndsi.Network(callbacks=(on_network_event,))
    n.start()

    import os
    import psutil
    pid = os.getpid()
    ps = psutil.Process(pid)
    ts = time.time()

    from pyglui import graph
    print graph.__version__
    cpu_g = graph.Line_Graph()
    cpu_g.pos = (50,100)
    cpu_g.update_fn = ps.cpu_percent
    cpu_g.update_rate = 5
    cpu_g.label = 'CPU %0.1f'

    fps_g = graph.Line_Graph()
    fps_g.pos = (50,100)
    fps_g.update_rate = 5
    fps_g.label = "%0.0f FPS"
    fps_g.color[:] = .1,.1,.8,.9

    on_resize(window,*glfwGetWindowSize(window))

    while not quit:
        try:
            dt,ts = time.time()-ts,time.time()
            clear_gl_screen()

            cpu_g.update()
            cpu_g.draw()
            fps_g.add(1./dt)
            fps_g.draw()

            gui.update()

            glfwSwapBuffers(window)
            glfwPollEvents()

            # handle ndsi
            while n.has_events:
                n.handle_event()
            for s in sensors.values():
                while s.sensor.has_notifications:
                    s.sensor.handle_notification()
        except (KeyboardInterrupt, SystemExit):
            global quit
            quit = True

    for sensor in sensors.values():
        sensor.cleanup()
    sensors = None
    n.stop()
    gui.terminate()
    glfwTerminate()
    logger.debug("Process done")

if __name__ == '__main__':
    runNDSIClient()

