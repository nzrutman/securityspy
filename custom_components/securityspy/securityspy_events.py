"""Wrapper that listens for Events from a SecuritySpy Surveillance Server
   Specifically developed to wotk with Home Assistant
   Developed by: @briis
   Github: https://github.com/briis/securityspy
   License: MIT
"""

import threading
import requests
from base64 import b64encode

class securityspyEvents:
    """ Class that reads the Event Stream from SecuritySpy """

    def __init__(self, host, port, User, Pass, ssl, callback=None):
        
        self._host = host
        self._port = port
        self._user = User
        self._pass = Pass
        self._auth_key = b64encode(bytes(self._user + ":" + self._pass,"utf-8")).decode()
        self._callback = callback

        print(self._auth_key)

    def event_listner(self):
        """ Threaded Event Lisner """

        url = "http://%s:%s/++eventStream?version=3&format=multipart&auth=%s" % (self._host, self._port, self._auth_key)
        events = requests.get(url, headers=None, stream=True)
        
        while self.running:
            try:                
                for line in events.iter_lines(chunk_size=200):
                    if not self.running:
                        break

                    if line:
                        event_data = {}
                        data = line.decode()
                        if data[:14].isnumeric():
                            event_arr = data.split(" ")
                            if event_arr[3] == "TRIGGER_M":
                                # Check what triggered the motion
                                object_type = "Video"
                                if event_arr[4] == "2":
                                    object_type = "Audio"
                                elif event_arr[4] == "128":
                                    object_type = "Human"
                                elif event_arr[4] == "256":
                                    object_type = "Vehicle"

                                item = {
                                    event_arr[2]: {
                                        "event_time": event_arr[0],
                                        "motion": True,
                                        "trigger_type": event_arr[4],
                                        "object_type": object_type,
                                    }
                                }
                                event_data.update(item)

                            elif event_arr[3] == "FILE":
                                item = {
                                    event_arr[2]: {
                                        "event_time": event_arr[0],
                                        "motion": False,
                                        "trigger_type": None,
                                        "object_type": None,
                                    }
                                }
                                event_data.update(item)
                                
                            if len(event_data) > 0 and self._callback:
                                self._callback(event_data)

            except Exception as ex:
                if self._callback:
                    self._callback(ex)

    def start_event_listner(self):
        """ Call this to start the receiver thread """
        self.running = True
        self.thread = threading.Thread(target = self.event_listner)
        self.thread.start()

    def stop_event_listner(self):
        """ Call this to stop the receiver """
        self.running = False
