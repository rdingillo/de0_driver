# -*- coding: utf-8 -*-
"""
Created on Wed Jun 08 10:57:08 2016

@author: Iain.Derrington
"""
import serial
import logging
import time
from PyQt5 import Qt
import ctypes as ct
import struct


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('DE0')


class SerialConf():
    """
    Helper class.
    Used by the DE0 constructor to initiate a serial port
    """

    def __init(self):
        """
        """
        self.port = None
        self.baud = None
        self.bits = 8
        self.stop = None
        self.parity = None


def float_to_hex(f):
    return hex(struct.unpack('<I', struct.pack('<f', f))[0])



class DE0():
    """
    Class DE0 encapsulates some of the functionality of Benoit's
    DE0 board.     
    """
    ERRORBITMASK = 0x80

    convertErrorCode = ["ERR_NONE", \
                        "ERR_TIMEOUT", \
                        "ERR_ABORT", \
                        "ERR_QUIT", \
                        "ERR_BUSY", \
                        "ERR_DIV_BY_ZERO", \
                        "ERR_INVALID_ARG", \
                        "ERR_WRONG_ARG_COUNT", \
                        "ERR_OVERFLOW", \
                        "ERR_INITIALISE_FAILED", \
                        "ERR_NOT_INITIALISED", \
                        "ERR_OPERATION_FAILED", \
                        "ERR_INVALID_DEVICE", \
                        "ERR_INVALID_CHANNEL", \
                        "ERR_UNKNOWN"]

    def __init__(self, SerialConf):
        """
        
        """
        logger.info("Create instance of DE0")
        self.portOpen = False
        self.mutex = Qt.QMutex()

    def openPort(self, serialconf):
        """
        """
        print("Opening COM Port")

        try:
            self.__ser = serial.Serial()
            self.__ser.port = serialconf.port
            self.__ser.baudrate = serialconf.baud
            self.__ser.bytesize = serialconf.bits
            self.__ser.parity = serialconf.parity
            self.__ser.stopbits = serialconf.stop

            if self.__ser.is_open:
                logger.info("Serial port already open")
            else:
                self.__ser.open()
                self.portOpen = True
        except serial.SerialException as e:
            self.portOpen = False
            logger.error("Failed to open serial port", e)

    def dummy(self):
        print("dummy")

    def close(self):
        """
        """
        try:
            self.__ser.close()
            self.portOpen = False
            self.mutex.unlock()
        except Exception:
            logger.error("Error closing serial port")

    # -----------------------------------------------------------   IO ACCESS ----------------------------------------------

    def writeIO(self, address, data):
        """
        Writes data to io register address
        """
        if self.portOpen is False:
            logger.info("Serial port not open")
            return

        dataPckt = [0x02, 0x00, 0x04]

        dataPckt.append((address >> 8) & 0x00ff)
        dataPckt.append(address & 0x00ff)

        dataPckt.append((data >> 8) & 0x00ff)
        dataPckt.append(data & 0x00ff)

        self.mutex.lock()
        self.__ser.write(dataPckt)
        result = bytearray(self.__ser.read(4))
        self.mutex.unlock()

        if (len(result) > 3):
            if result[3] == 0:
                return True
            else:
                return False

    # ----------------------------------------------------------------------------------------------------------------------
    def readIO(self, address):
        """
        """

        if self.portOpen is False:
            logger.info("readIO(): Serial port not open!")
            return

        dataPckt = [0x02, 0x00, 0x02]

        dataPckt.append((address >> 8) & 0x00ff)
        dataPckt.append(address & 0x00ff)

        self.mutex.lock()
        self.__ser.write(dataPckt)
        result = bytearray(self.__ser.read(5))
        self.mutex.unlock()

        if (len(result) > 3):
            if result[0] == 2:
                return (result[3] << 8) + result[4]
            else:
                return False

        # ----------------------------------------------------------------------------------------------------------------------

    def writeIO32(self, address, data):
           """
           Writes data to io register address
           """
           if self.portOpen is False:
               logger.info("Serial port not open")
               return

           dataPckt = [0x02, 0x00, 0x06]

           dataPckt.append((address >> 8) & 0x00ff)
           dataPckt.append(address & 0x00ff)

           dataPckt.append((data >> 24) & 0x000000FF)
           dataPckt.append((data >> 16) & 0x000000FF)
           dataPckt.append((data >> 8) & 0x000000FF)
           dataPckt.append(data & 0x000000FF)

           self.mutex.lock()
           self.__ser.write(dataPckt)
           result = bytearray(self.__ser.read(4))
           self.mutex.unlock()

           if (len(result) > 3):
               if result[3] == 0:
                   return True
               else:
                   return False

        # ----------------------------------------------------------------------------------------------------------------------
    def readIO32(self, address):
           """
           """

           if self.portOpen is False:
               logger.info("readIO(): Serial port not open!")
               return

           dataPckt = [0x02, 0x00, 0x02]

           dataPckt.append((address >> 8) & 0x00ff)
           dataPckt.append(address & 0x00ff)

           self.mutex.lock()
           self.__ser.write(dataPckt)
           result = bytearray(self.__ser.read(7))
           self.mutex.unlock()

           if (len(result) > 3):
               if result[0] == 2:
                   return (result[3] << 24) + (result[4] << 16) + (result[5] << 8) + (result[6])
               else:
                   return False

    # ----------------------------------------------------------------------------------------------------------------------

    def getFwVersion(self):
        """
        """
        if self.portOpen is False:
            logger.info("Serial port not open")
            return False

        dataPckt = [0x01, 0x00, 0x01, 0xf2]

        self.mutex.lock()
        self.__ser.write(dataPckt)
        result = bytearray(self.__ser.read(5))
        self.mutex.unlock()

        # make sure at least one byte has been returned

        if (len(result) > 2):
            if (result[0] & DE0.ERRORBITMASK):
                logger.info("Write: " + str(bytearray(dataPckt)))
                logger.info("Read: " + str(result))
                logger.error("Failed to get version: ", DE0.convertErrorCode[result[2]])
                raise Exception(DE0.convertErrorCode[result[2]])
            else:
                return ("%s,%s" % (result[3], result[4]))
        else:
            logger.info("Write: " + str(bytearray(dataPckt)))
            logger.info("Read: " + str(result))
            logger.error("Failed to get version: Serial port timed out.")
            raise Exception("Failed to get version: Serial port timed out.")


if __name__ == "__main__":
    mySerConf = SerialConf()
    mySerConf.port = 'COM15'
    mySerConf.baud = 115200
    mySerConf.bits = 8
    mySerConf.stop = 1
    mySerConf.parity = serial.PARITY_NONE

    myDE0 = DE0(mySerConf)

    myDE0.openPort(mySerConf)


    myDE0.writeIO(0x2006, 0x0001)
    result = myDE0.readIO(0x2006)
    print(result)

    myDE0.writeIO(0x2006, 0x0000)
    result = myDE0.readIO(0x2006)
    print(result)



    # ------------------  32 Bit Access
    print("WRITE SECTION 32 Bit ACCESS")
    # WRITE PHASE_1P_mV_TO_DAC @ 0x6099

    PHASE_1P_mV_TO_DAC_addr = 0x6099

    value_Volts = 1.608
    value_mV = value_Volts * 1000

    value_mV_Hex_with_0x = float_to_hex(value_mV)
    print(value_mV_Hex_with_0x)

    value_mV_Int = int(value_mV_Hex_with_0x, 16)
    print(value_mV_Int)


    myDE0.writeIO32(PHASE_1P_mV_TO_DAC_addr, value_mV_Int)

    print("")
    print("")
    print ("READ BACK SECTION 32 Bit ACCESS")
    #READ BACK PHASE_1P_DAC_TO_mV @ 0x60AC

    PHASE_1P_DAC_TO_mV_addr = 0x60AC

    result = (myDE0.readIO32(PHASE_1P_DAC_TO_mV_addr))

    resultHex_with_0x = hex(result)
    print(resultHex_with_0x)

    resultHex_No_0x = f'{result:x}'
    print(resultHex_No_0x)

    resultfloat = struct.unpack('!f', bytes.fromhex(resultHex_No_0x))[0]
    print(resultfloat)   #mVolts

    resultfloatScaled =resultfloat / 1000

    #print(resultfloatScaled)  # Volts
    print("%.3f" %resultfloatScaled + " Volts") #Volts



    # ------------------  Get Fw Version

    result = myDE0.getFwVersion()
    print("Fw Version " + result)

    myDE0.close()
