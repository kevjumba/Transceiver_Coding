from smbus2 import SMBusWrapper
import sys
import time
i2c_addr = 0x50
i2c_auth_addr = 0x51
auth_offset =0x7B

password = [0x12, 0x34, 0x56, 0x78]
block = [0x32, 0x36, 0x31, 0x33, 0x35, 0x38]
def read_block(addr, registry, length):

    register = int(registry) #decimal form of starting registry
    with SMBusWrapper(1) as bus:
        data = []
        index = 0
        if length>16:
            while length > 16:
                #print("reading from ", register, "for length", 32)
                data = data + bus.read_i2c_block_data(addr, register+16*index, 16)
                length = length-16
                index+=1
                time.sleep(0.02)
        #print("reading bus at", register+16*index, "for length", length)
        data= data + bus.read_i2c_block_data(addr, register+16*index, length)
        return data
    """
    with SMBusWrapper(1) as bus:
        data = []
        index = 0
        for i in range(0, length):
            data= data + bus.read_i2c_block_data(addr, register+i*2, 1)
            time.sleep(0.05)
        return data
    """

if(__name__ == '__main__'):
    with SMBusWrapper(1) as bus:
        a=bus.read_i2c_block_data(0x50, 0x00, 4)
    
    print a
    
    exit()
    
#    data = read_block(i2c_addr, int(sys.argv[1]), int(sys.argv[2]))
    hex_list = ['{0:02X}'.format(x) for x in data]
    hex_str = ''.join(hex_list)
    print(hex_str)


