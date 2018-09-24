
from smbus2 import SMBusWrapper
import sys
import math
import time
i2c_addr = 0x50
offset = 0x54
i2c_auth_addr = 0x51
auth_offset =0x7B

password = [0x12, 0x34, 0x56, 0x78]
block = []
def write_block(addr, registry, byte_string):
    with SMBusWrapper(1) as bus:
        try:
            #print("writing to i2c...")
            #bus.write_i2c_block_data(i2c_auth_addr, auth_offset, password)
            block = [int(byte_string[i:i+2], 16) for i in range(0, len(byte_string), 2)]
            register_num = int(registry)
            start = register_num #decimal form of starting registry
            nearest_register = math.ceil(start/8.0)*8
            first_write_len = int(nearest_register - start)
            """write first bytes"""
            #print("writing block ")
            #print map("{0:02X}".format, [int(i) for i in block[0:first_write_len]])
            if first_write_len > 0:
                bus.write_i2c_block_data(addr, register_num, block[0:first_write_len])
                time.sleep(0.01)
            index = 0
            while len(block)-first_write_len-index*8>=8:
                temp_register = start + first_write_len + index*8
                bus.write_i2c_block_data(addr, temp_register, block[first_write_len+index*8: first_write_len + index*8+8])
                time.sleep(0.04)
    #            print("writing block ")
    #            print map("{0:02X}".format, [int(i) for i in block[first_write_len+index*8: first_write_len + index*8 + 8]])
                index = index+1
            last_write_len = len(block)-first_write_len - index*8
            last_register = start + first_write_len + index*8
            if last_write_len>0:
                bus.write_i2c_block_data(addr, last_register, block[first_write_len + index*8: first_write_len + index*8 + last_write_len])
#            print("Write to address:", i2c_addr, "at registry: ", registry, "successful")
    #        print("writing block ")
    #        print map("{0:02X}".format, [int(i) for i in block[first_write_len + index*8: first_write_len + index*8 + last_write_len]])
        except Exception, e:
            print("Error! Exception", e)
            print("Suggestions: Check that the board is connected to the Pi and" \
            " that you are writing the password to the transceiver")

def main():
	write_block(i2c_addr, sys.argv[1], sys.argv[2])

if __name__ == "__main__":
	main()


