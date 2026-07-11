from matplotlib.animation import FuncAnimation
import time
import threading

class live_plotter:
    def __init__(self, fig, ax, lines, dynamic_data, bar_container, frame_update):
         self.fig = fig
         self.ax = ax
         self.lines = lines
         self.dynamic_data = dynamic_data
         self.bar_container = bar_container
         self.frame_update = frame_update
         self.lock = threading.Lock()
         self.last_frame = -1
         self.ani = FuncAnimation(self.fig, self.update, frames=self.frame_generator, blit=False, interval=500)
         
    def update(self, frame):
        with self.lock:
            if frame == 0 and self.last_frame == 0:
                return self.lines.values()
                
            self.last_frame = frame

            return self.frame_update(self.ax, self.dynamic_data, self.lines, self.bar_container)

    def add_frame(self, new_data):
        with self.lock:
            self.dynamic_data.loc[len(self.dynamic_data)] = new_data
            self.ax.set_xlim(1, len(self.dynamic_data)) 
        
    def frame_generator(self):
        frame = 0
        while True:
            yield frame
            frame += 1
            time.sleep(0.1)

    def stop_animation(self):
        print("Stopping animation...")
        self.ani.event_source.stop()