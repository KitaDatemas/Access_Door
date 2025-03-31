import serial

ser = serial.Serial('COM14', 9600)  # Replace COM3 with your actual port
# for i in range(0,100):
ser.write(b'Hello!\n')  # Send data
    # response = ser.readline()  # Read response
    # print(response.decode())
ser.close()