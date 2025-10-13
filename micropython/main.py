import cbor2
import asyncio
import aioble
import bluetooth
import time
import machine

_WENET_SERVICE_UUID = bluetooth.UUID('fb63feb8-31ad-451d-a587-9fc20f9c8add')
_WENET_CHAR_UUID = bluetooth.UUID('3d235f0e-61f8-4455-89c6-2f7d73c33178')

_NUS_SERVICE_UUID = bluetooth.UUID('6E400001-B5A3-F393-E0A9-E50E24DCCA9E')
_NUS_TX_CHAR_UUID = bluetooth.UUID('6E400003-B5A3-F393-E0A9-E50E24DCCA9E')

# How frequently to send advertising beacons.
_ADV_INTERVAL_MS = 250_000

# Register Wenet Service
temp_service = aioble.Service(_WENET_SERVICE_UUID)
temp_characteristic = aioble.Characteristic(
    temp_service, _WENET_CHAR_UUID, read=True, notify=True
)

# Register Nordic UART Service
nus_service = aioble.Service(_NUS_SERVICE_UUID)
nus_tx_characteristic = aioble.Characteristic(
    nus_service, _NUS_TX_CHAR_UUID, read=False, notify=True
)

aioble.register_services(temp_service, nus_service)

def build_packet(packet_dict):
    packet = cbor2.dumps(packet_dict)
    # Need binary packet to be less than 254 bytes to fit in wenet telemetry frame
    assert(len(packet) <= 254)
    return packet

def get_iso_timestamp():
    rtc = machine.RTC()
    now = rtc.datetime()
    ms = time.time_ns() // 1_000_000 % 1000
    return f"{now[0]}-{now[1]:02}-{now[2]:02}T{now[4]:02}:{now[5]:02}:{now[6]:02}.{ms:03}+00:00"

# Simulated data packets
# In a real sensor, you would gather actual data to send
async def sensor_task():
    sensor_name = "neck_sensor"
    voltage = 3.30
    temperature = 70.0
    humidity = 50.0
    pressure = 10.0
    while True:
        # Create a python dictionary with the sensor data
        # Fields time and id are mandatory
        packet_dict = {'time': get_iso_timestamp(),'id':sensor_name, 'voltage':voltage, 'temperature': temperature, 'humidity': humidity, 'pressure': pressure}
        
        # Simulate some changing sensor data
        humidity += 1.5
        temperature += 1.2
        voltage += 0.1
        pressure += 0.05
        if humidity > 60:
            humidity = 50.0
        if voltage > 4.3:
            voltage = 3.3
        if temperature > 80:
            temperature = 70.0
        if pressure > 20:
            pressure = 10.0
        
        # Build the binary json packet
        cbor_packet = build_packet(packet_dict)
        print(packet_dict)
        print(f"BLE packet length: {len(cbor_packet)}")
        
        # Transmit
        nus_tx_characteristic.write(cbor_packet, send_update=True)
        await asyncio.sleep_ms(1000)
        
        
# Serially wait for connections. Don't advertise while a central is
# connected.
async def peripheral_task():
    while True:
        async with await aioble.advertise(
            _ADV_INTERVAL_MS,
            name="WenetPico",
            services=[_WENET_SERVICE_UUID],
        ) as connection:
            print("Connection from", connection.device)
            await connection.disconnected(timeout_ms=None)

# Run both tasks.
async def main():
    t1 = asyncio.create_task(sensor_task())
    t2 = asyncio.create_task(peripheral_task())
    await asyncio.gather(t1, t2)

asyncio.run(main())
