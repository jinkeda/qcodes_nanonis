# -*- coding: utf-8 -*-
"""
Created on Thu Aug 17 17:36:23 2023

@author: k.jin
"""
import os
import time
from qcodes.instrument import IPInstrument, InstrumentBase
from qcodes.instrument.parameter import Parameter,ParameterWithSetpoints
import re
import ast
import json
import struct
import logging
import warnings
from typing import Dict,List,Union,Any,Tuple
import numpy as np
from itertools import product
import struct
from qcodes import logger
import qcodes.validators as vals

from qcodes.utils.validators import Arrays

log = logging.getLogger(__name__)

Nanonis_LOGGER = '.'.join((InstrumentBase.__module__, 'com', 'visa'))
logger.get_log_file_name()


class NanonisIPInstrumentbase(IPInstrument):
    def __init__(self, name:str, configpath:str, timeout =  float(0.1*60), **kwargs:Any) -> None:

        # Loading command lists from JSON files (as in the NanonisInterface)
        #self. configpath =  'O:/AG/Lüpke/2D lab/Keda Jin/script/qc_nanonis/configuration/'
        self. configpath = configpath
        self.commandList = self.loadCommandList('commands_new.json')
        print('yes')
        #self.special_commands = self.loadCommandList("special_commands.json")
        self.config = self.loadCommandList('sigma.json')
        
        self.TCP_info = self.get_TCP_info()

        super().__init__(name = name, address = self.TCP_info['IP-Adress'], port = self.TCP_info['Port'],timeout = timeout,  **kwargs)
        self._buffer_size = 1024*1024
        self.nanonis_log = logger.get_instrument_logger(self, Nanonis_LOGGER)
        
    
    def loadCommandList(self, filename: str) -> dict:
        filepath = os.path.join(self.configpath,filename)
        with open(filepath, "r") as cmd_file:
            commandList = json.load(cmd_file)
        return commandList
        
    
    def get_TCP_info(self):
        TCP_info = {}
        TCP_info['IP-Adress'] = self.config['Interface']['IP-Adress']
        TCP_info['Port'] = self.config['Interface']['Port']
        print('IP:',TCP_info['IP-Adress'])
        print('port:',TCP_info['Port'])
        print('Connected!')

        return TCP_info


    def encode_request_message(self, cmd_name: str, arg_values: Dict[str, Union[int, float, str,List[int]]], arg_types: Dict[str, str]) -> bytes:
        """Encodes a command including arguments into a byte array that can be interpreted 
        by the Nanonis software. For syntax of the request messages, see pages 23-29 in 
        the Nanonis TCP Protocol.

        Args:
            cmd_name (str): Name of the executed command.
            send_response (int): Defines if the server sends a message back (=1) or not (=0).
            arg_values (dict): Argument values.
            arg_types (dict): Argument types according to Number Formatting Type.

        Returns:
            bytes: Encoded request message.
        """
        request = b''
        body = b''
        if len(arg_values) > 0:
       #     for key, value in arg_values.items():
       #         if arg_types[key] != 's':
       #             arg = self.convert_number_to_byte(value, arg_types[key])
       #             body += arg
       #         else:
       #             arg = value.encode()
       #             body += arg
            previous_value = None
    
            for key, value in arg_values.items():
                value_type = arg_types[key]
                if value_type == 's':
                # Encode string
                    arg = value.encode()
                    body += arg
                elif value_type == "1D array int":
                # Encode 1D array of integers
                    format_string = f'>{previous_value}i'  # Format string for an array of integers
                    arg = struct.pack(format_string, *value)
                    body += arg
                else:
                # Encode single number
                    arg = self.convert_number_to_byte(value, value_type)
                    body += arg
                previous_value = value


        cmd = self.convert_string_to_byte(cmd_name, 32)
        body_size = self.convert_number_to_byte(len(body), 'i')
        send_response= self.convert_number_to_byte(1, 'h')
        not_used = self.convert_number_to_byte(0, 'h')
        request = cmd + body_size + send_response + not_used + body
        return request

    def decodeResponseMessage(self, resp, respTypes):
        """Decodes a response message from the Nanonis software. 
        Currently only single values can be decoded. Arrays are not yet supported.

        Args:
            resp (bytes): Response message from Nanonis.
            respTypes (dict): Response types according to Number Formatting Types.

        Returns:
            dict: Decoded response message.
        """        
        headerSize = 40 # Fixed
        index = headerSize
        decodedResp = {}
        for key, value in respTypes.items():
            size = len(self.convertNumberToByte(0, value))
            decodedResp[key] = self.convert_bytes_to_number(resp[index:index+size], value)
            index += size
        return decodedResp

    def convert_string_to_byte(self,cmd, size) -> bytes:
        """Converts a string to a bytes object. 
        Byte object is padded with zeros until the length equals 'size'.

        Args:
            cmd (str): String to be converted.
            size (int): Size of byte-array.

        Returns:
            byte: Converted string as bytes object.
        """        
        cmd_bytes = cmd.encode()
        if len(cmd_bytes) < size:
            num_pads = size - len(cmd_bytes)
            for _ in range(num_pads):
                cmd_bytes += bytes([0])
        return cmd_bytes

    
    def convert_number_to_byte(self,num, numType) -> bytes:
        """Converts a number into a byte object (big-endian).

        Args:
            num (int, float, etc.): Any number that is accepted by struct.pack().
            numType (str): Format type according to the module struct().

        Returns:
            bytes: Converted number as bytes object.
        """        
        conv_format = '>{}'.format(numType)
        num_bytes = struct.pack(conv_format, num)
        return num_bytes

    def convert_bytes_to_number(self, numBytes: bytes, numType: str) -> Union[int, float]:
        """Converts a bytes object (big-endian) into a number.

        Args:
            numBytes (bytes): Bytes object to be converted.
            numType (str): Format type according to the module struct().

        Returns:
            int, float, etc.: Number. Type according to specified Number Formatting Type.
        """        
        conv_format = '>{}'.format(numType)
        num = struct.unpack(conv_format, numBytes)[0]
        return num

    def encoed_command(self,cmdAlias:str, cmdArgs:list) -> bytes:
        """
        Encode the Command in the  Command list to the request_message
        """
        resp = ''
        err = False
        #print(cmdAlias, cmdArgs)

        if not cmdAlias in self.commandList:
            raise RuntimeError(f'Command {cmdAlias} is not in the commandlist'.format(cmdAlias))

        cmdDetail = self.commandList[cmdAlias]
        cmdName = cmdDetail['cmdName']
        argTypes = cmdDetail['argTypes']
        argValues = cmdDetail['argValues']

        len_cmdArgs_given = len(cmdArgs)
        len_cmd_required =  len(cmdDetail['args'])

        if not len_cmdArgs_given ==len_cmd_required:
            raise ValueError (f'Command {cmdAlias} needs {len_cmd_required} arguments , but {len_cmdArgs_given} is given.')

        if len_cmd_required > 0:
            prev_arg = None
            for index,arg in enumerate(self.commandList[cmdAlias]['args']):
                if argTypes[arg] == 's':
                    argValues[arg] = str(cmdArgs[index])
                    argValues[prev_arg] = len(argValues[arg])                    
                elif argTypes[arg] == 'I':
                    argValues[arg] = int(cmdArgs[index])
                elif argTypes[arg] == 'i':
                    argValues[arg] = int(cmdArgs[index])
                elif argTypes[arg] == 'H':
                    argValues[arg] = int(cmdArgs[index])
                elif argTypes[arg] == 'f':
                    argValues[arg] = float(cmdArgs[index])
                elif argTypes[arg] == '1D array int':
                    argValues[arg] = [int(element) for element in cmdArgs[index]]
                    argValues[prev_arg] = len(argValues[arg])
                else:
                    raise ValueError('no defined type of the argument')
                prev_arg = arg
        encoed_cmd = self.encode_request_message(cmd_name = cmdName,  arg_values = argValues, arg_types = argTypes)
        return encoed_cmd

    def _send(self,encoded_message: bytes) -> None:

        # Ensure that the socket connection is established
        if self._socket is None:
            raise RuntimeError(f'IPInstrument {self.name} is not connected')

        self.nanonis_log.debug(f"Writing {encoded_message} to instrument {self.name}")
        self._socket.sendall(encoded_message)

    
    def _recv(self, num_bytes=1024) -> bytes:
        """
        Receive data from the Nanonis instrument.

        Args:
            num_bytes (int, optional): The number of bytes to read. If None, read all available data.

        Returns:
            bytes: The received data.
        """
        if self._socket is None:
            raise RuntimeError(f'IPInstrument {self.name} is not connected')
            
        response = self._socket.recv(num_bytes)
        if response == b'':
            warnings.warn("Received an empty response from the instrument.")

        return response


    
    def write(self,cmd:str) -> None:
        """
        Write a command string with NO response to the hardware.
        formate of cmd: do arg1 arg2 arg3 
        """
        parts = cmd.split()
        head = parts[0]
        args = [self.convert_string_to_list(arg) for arg in parts[1:]]
        try:
            self.write_raw(head,args)
        except Exception as e:
            inst = repr(self)
            e.args = e.args + ("writing " + repr(cmd) + " to " + inst,)
            raise e
    
    def ask(self, cmd:str):
        """
        Write a command string to the hardware and return a response.
        formate of cmd: do arg1 arg2 arg3 
        """
        parts = cmd.split()
        head = parts[0]
        if len(parts)==1:
            args = []
        else:
            args = [self.convert_string_to_list(arg) for arg in parts[1:]]
        try:
            answer = self.ask_raw(head,args)
            return answer

        except Exception as e:
            inst = repr(self)
            e.args = e.args + ("asking " + repr(cmd) + " to " + inst,)
            raise e

    def write_raw(self,cmdAlias: str, cmdArgs: list) -> None:
        """
        Low-level interface to send a command that gets no response.

        Args:
            cmdAlias: The command to send to the instrument.
        """
        encoed_cmd = self.encoed_command(cmdAlias = cmdAlias, cmdArgs = cmdArgs)
        with self._ensure_connection:
            self._send(encoed_cmd)
            #if self._confirmation:
            receive_message = self._recv(self._buffer_size)[40:]
            error = int.from_bytes(receive_message[40:48],byteorder='big')
            
            if error:
                error_message = receive_message[48:]
                raise RuntimeError(error_message)

  
    def ask_raw(self,cmdAlias: str, cmdArgs: list) -> str:
        """
        Low-level interface to send a command an read a response.

        Args:
            cmd: The command to send to the instrument.

        Returns:
            The instrument's string response.
        """
        encoed_cmd = self.encoed_command(cmdAlias = cmdAlias, cmdArgs = cmdArgs)
        with self._ensure_connection:
            self._send(encoed_cmd)
            response = self._recv(self._buffer_size)

            
            try:
                decode_response =  self.parse_response_with_command_dict (response = response ,cmdAlias= cmdAlias )
            except: 
                print('can not decode the message!')
                return response
            checker_cmd_name =  decode_response['cmd_name']
            if not checker_cmd_name == self.commandList[cmdAlias]['cmdName']:
                raise RuntimeError(f'wrong response command. {cmdAlias} asked, but {checker_cmd_name} get.')

            return decode_response


            #return self._recv(1024*8)
    def convert_string_to_list(self,component: str) -> Union[str, List[int]]:
        """Converts a string representation of a list to an actual Python list."""
        list_pattern = re.compile(r'\[.*?\]')
    
        # Check if the component matches the list pattern
        if list_pattern.fullmatch(component):
            try:
                # Convert the string representation of the list to an actual list
                real_list = ast.literal_eval(component)
                return real_list
            except (SyntaxError, ValueError):
            # If conversion fails, return the component as is
                return component
        else:
        # If not a list pattern, return the component as is
            return component


    def parse_response_with_command_dict(self, response: bytes, cmdAlias: str) -> Dict[str, object]:
        command_dict = self.commandList[cmdAlias]
    
        # Extract the header components
        cmd_name = response[:32].decode('utf-8').rstrip('\x00')

        body_size = int.from_bytes(response[32:36], byteorder='big')

        # Extract the body
        body = response[40:40 + body_size]

        # Extract the error status and error size from the last 8 bytes of the body
        error_size_in_bytes = int.from_bytes(body[-4:], byteorder='big')
        error_status = int.from_bytes(body[-8:-4], byteorder='big')

        if error_status:
            error_code, error_message = self.decode_error_message(body)
            print('error_code:', error_code)
            raise RuntimeError(error_message)

        result = {
            'cmd_name': cmd_name,
            'body_size': body_size,
            'error_size_in_bytes': error_size_in_bytes,
            'error_status': error_status,
        }

        offset = 0
        last_two_keys = [None, None] ## for receive the array size
        respTypes = command_dict["respTypes"]
    
        for key, value_type in respTypes.items():
            if len(value_type) == 1:  # Single-letter format character
                if value_type == "s":
                    stringsize = result[last_two_keys[1]]
                    struct_format =  f"{stringsize}s"
                    size = struct.calcsize(struct_format)
                    value_bytes = body[offset:offset+size]
                    value = struct.unpack(struct_format, value_bytes)
                    result[key] = value[0].decode('utf-8', errors='replace')
                    offset += size
                    
                else:
                    struct_format = '>' + value_type
                    size = struct.calcsize(struct_format)
                    value_bytes = body[offset:offset+size]
                    value, = struct.unpack(struct_format, value_bytes)
                    result[key] = value
                    offset += size
             
                last_two_keys[0] = last_two_keys[1]
                last_two_keys[1] = key

            elif value_type == "1D array string" and last_two_keys[1]:
                num_elements_key = last_two_keys[1]
                num_elements = result[num_elements_key]
                strings, offset = self.decode_1d_array_string(body, offset,num_elements)
                result[key] = strings
                
                
            elif value_type == "2D array float32" and last_two_keys[0] and last_two_keys[1]:
                num_rows_key = last_two_keys[0]
                num_cols_key = last_two_keys[1]
                num_rows = result[num_rows_key]
                num_cols = result[num_cols_key] 
                array_2d, offset = self.decode_2d_array_num(body, offset,num_rows, num_cols,'f')
                result[key] = array_2d

            elif value_type == "1D array float32":
                num_element_key = last_two_keys[1]
                num_element = result[num_element_key]
                array_1d, offset = self.decode_2d_array_num(body,offset, 1,num_element,'f')
                result[key] = array_1d

            elif value_type == "1D array int":
                num_element_key = last_two_keys[1]
                num_element = result[num_element_key]
                array_1d, offset = self.decode_2d_array_num(body,offset, 1,num_element,'i')
                result[key] = array_1d.astype(int)
    
        return result

    def decode_1d_array_string(self,body: bytes, offset: int, num_elements: int)-> Tuple[List[str], int]:
        strings: List[str] = []
        for _ in range(num_elements):
            string_size = struct.unpack('>i', body[offset:offset+4])[0]
            offset += 4
            string_bytes = body[offset:offset+string_size]
            string_value = string_bytes.decode('utf-8', errors='replace')
            strings.append(string_value)
            offset += string_size
        return strings, offset

    def decode_2d_array_num(self,response: bytes, offset: int, num_rows: int, num_cols: int,format:str)-> Tuple[np.ndarray, int]:
        array_2d = np.empty((num_rows, num_cols), dtype=np.float32)
        for row, col in product(range(num_rows), range(num_cols)):
            value_bytes = response[offset:offset+4]
            value, = struct.unpack(f'>{format}', value_bytes)
            array_2d[row, col] = value
            offset += 4
        return array_2d, offset



    def decode_error_message(self, response_bytes: bytes) -> (int, str):
    # Unpack the integer error code (4 bytes, big-endian)
        error_code = struct.unpack('>I', response_bytes[24:28])[0]

    # Extract the error message (starting from byte 28)
        error_message_bytes = response_bytes[28:]
        error_message = error_message_bytes.decode('utf-8')

        return error_code, error_message


    def parse_request_with_command_dict(self, request: bytes, cmdAlias: str) -> Dict[str, object]:
        """
        debug the request command
        """

        command_dict = self.commandList[cmdAlias]
    
        # Extract the header components
        cmd_name = request[:32].decode('utf-8').rstrip('\x00')

        body_size = int.from_bytes(request[32:36], byteorder='big')

        # Extract the body
        body = request[40:40 + body_size]

        # Extract the error status and error size from the last 8 bytes of the body

        

        result = {
            'cmd_name': cmd_name,
            'body_size': body_size,
        }

        offset = 0
        last_two_keys = [None, None] ## for receive the array size
        argTypes = command_dict["argTypes"]
    
        for key, value_type in argTypes.items():
             # Single-letter format character
            if value_type == "s":
                stringsize = result[last_two_keys[1]]
                struct_format =  f"{stringsize}s"
                size = struct.calcsize(struct_format)
                value_bytes = body[offset:offset+size]
                value = struct.unpack(struct_format, value_bytes)
                result[key] = value[0].decode('utf-8', errors='replace')
                offset += size   
            elif value_type == "1D array int":
                num_element_key = last_two_keys[1]
                num_element = result[num_element_key]
                array_1d, offset = self.decode_2d_array_num(body,offset, 1,num_element,'i')
                result[key] = array_1d.astype(int)

            else:
                struct_format = '>' + value_type
                size = struct.calcsize(struct_format)
                value_bytes = body[offset:offset+size]
                value, = struct.unpack(struct_format, value_bytes)
                result[key] = value
                offset += size
                last_two_keys[0] = last_two_keys[1]
                last_two_keys[1] = key

      
    
        return result
    


