#!/usr/bin/python3

# lmg95.py
#
# Implement interface to ZES Zimmer LMG95 1 Phase Power Analyzer
# via RS232-Ethernet converter
#
# 2012-07, Jan de Cuveland, Dirk Hutter

import socket, telnetlib, time

EOS = b"\r\n"
TIMEOUT = 3
ECHO = True
DEBUG=False
#
# class scpi_socket:
#     def __init__(self, host = "", port = 0):
#
#         self._s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
#         if port > 0:
#             self.connect(host, port)
#
#     def connect(self, host, port):
#         self._s.connect((host, port))
#         self._s.settimeout(TIMEOUT)
#
#     def send(self, msg):
#         self._s.sendall(msg + EOS)
#
#     def recv_str(self):
#         response = ""
#         while response[-len(EOS):] != EOS:
#             try:
#                 response += self._s.recv(4096)
#             except socket.timeout as e:
#                 print( "error:", e)
#                 return ""
#         return response[:-len(EOS)]
#
#     def send_cmd(self, cmd):
#         result = self.query(cmd + ";*OPC?")
#         if result != "1":
#             print( "opc returned unexpected value:", result)
#
#     def send_brk(self, ctrl):
#         pass
#
#     def query(self, msg):
#         self.send(msg)
#         return self.recv_str()
#
#     def close(self):
#         self._s.close()
#
#     def __del__(self):
#         self.close()
#
#
# class scpi_telnet:
#
#     def __init__(self, host = "", port = 0): 
#         self._t = telnetlib.Telnet() 
#         if port > 0:
#             self.connect(host, port)
#
#     def connect(self, host, port):
#         self._t.open(host, port, TIMEOUT)
#
#     def close(self): 
#         self._t.close()
#
#     def recv_str(self):
#         response = self._t.read_until(EOS, TIMEOUT)
#         if response[-len(EOS):] != EOS:
#             print( "error: recv timeout")
#         return response[:-len(EOS)]
#
#     def send(self, msg):
#         self._t.write(msg + EOS)
#
#     def send_raw(self, msg):
#         self._t.get_socket().sendall(msg)
#
#     def query(self, cmd): 
#         self.send(cmd) 
#         return self.recv_str()
#
#     def send_cmd(self, cmd):
#         result = self.query(cmd + ";*OPC?")
#         if result != "1":
#             print( "opc returned unexpected value:", result)
#
#     def send_brk(self):
#         self.send_raw(chr(255) + chr(243))
#
#     def get_socket(self):
#         return self._t.get_socket()
#
#     def __del__(self):
#         self.close()

import serial
class scpi_serial:

    def __init__(self,  port):
        if type(port) == str:
            self._device= port 
            self.connect(port)


    def connect(self,  port):
        self._s = serial.Serial(port, 115200, bytesize=8, parity='N', stopbits=1, rtscts=False)
        self._s.timeout = TIMEOUT

    def close(self): 
        print( "c!")
        self._s.close()

    def flush(self):
        self._s.reset_input_buffer()
        self._s.reset_output_buffer()

    def recv_str(self):
        response=b""
        while response[-len(EOS):] != EOS:
            r=self._s.read(1)
            if len(r) < 1:
                # if DEBUG:
                #     print(response)
                    # print( "R:",len(response),response,'\n',":".join("{:02x}".format(ord(c)) for c in response))
                return response 
            response = response + r 
        if DEBUG:
            print(response)
            # print( "r:",response.strip(), "\n", ":".join("{:02x}".format(ord(c)) for c in response))
#        print( "r:",len(response),response,":".join("{:02x}".format(ord(c)) for c in response))
        return response[:-len(EOS)]

    def send(self, msg):
        if DEBUG:
            print( "w:", msg)
        _msg = msg + EOS
        self._s.write(_msg)
        if ECHO:
            response=self._s.read(len(_msg))
            if DEBUG:
                print(response)
                # print( "s: ",":".join("{:02x}".format(ord(c)) for c in response))

    def send_raw(self, msg):
        #self._s.get_socket().sendall(msg)
        if DEBUG:
            print( "W:", msg)
        self._s.write(msg)
        if ECHO:
            response=self._s.read(len(msg+EOS))
            if DEBUG:
                print(response)
                # print( "S: ",":".join("{:02x}".format(ord(c)) for c in response))

    def query(self, cmd): 
        self.send(cmd) 
        return self.recv_str()

    def send_cmd(self, cmd):
        result = self.query(cmd + b";*OPC?")
        if result != "1":
            print( "opc returned unexpected value: %s (len=%d)" %( result, len(result)))

    def send_brk(self):
        self.send_raw(b"\xff\xf3")

    def get_socket(self):
        return self._s

    def __del__(self):
        self.close()


class lmg95(scpi_serial):
    _short_commands_enabled = False

    def reset(self):
        self.flush()
        time.sleep(1.0)
        self.send_brk()
        time.sleep(1.0)
        self.send_cmd(b"*cls")
        self.send_cmd(b"*rst")
    
    def goto_short_commands(self):
        if not self._short_commands_enabled:
            self.send(b"syst:lang short")
        self._short_commands_enabled = True

    def goto_scpi_commands(self):
        if self._short_commands_enabled:
            self.send(b"lang scpi")
        self._short_commands_enabled = False

    def send_short(self, msg):
        self.goto_short_commands()
        self.send(msg)

    def send_scpi(self, msg):
        self.goto_scpi_commands()
        self.send(msg)

    def send_short_cmd(self, cmd):
        self.goto_short_commands()
        self.send_cmd(cmd)

    def send_scpi_cmd(self, cmd):
        self.goto_scpi_commands()
        self.send_cmd(cmd)

    def query_short(self, msg):
        self.goto_short_commands()
        return self.query(msg)

    def query_scpi(self, msg):
        self.goto_scpi_commands()
        return self.query(msg)

    def goto_local(self):
        self.send(b"gtl")

    def read_id(self):
        return self.query(b"*idn?")

    def beep(self):
        self.send_short_cmd(b"beep")

    def read_errors(self):
        return self.query_scpi(b"syst:err:all?")

    def set_ranges(self, current, voltage):
        self.send_short_cmd(b"iam manual");
        self.send_short_cmd(b"irng %d" % current)
        self.send_short_cmd(b"uam manual");
        self.send_short_cmd(b"urng %d" % voltage)

    def select_values(self, values):
        self.send_short(b"actn;" + b"?;".join(values) + b"?")

    def read_values(self):
        values_raw = self.recv_str().decode('ascii').strip()
        if len(values_raw) == 0:
            return []
        return [ float(x) for x in values_raw.split(";") ]

    def cont_on(self):
        self.send_short(b"cont on")

    def cont_off(self):
        self.send_short(b"cont off")
        
    def disconnect(self):
        self.read_errors()
        self.goto_local()
