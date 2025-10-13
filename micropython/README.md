# Wenet BLE Sensor Micropython Example

This example shows a simulated sensor sending data to the Wenet BLE modem using CBOR packets. CBOR packets are essentially a binary version of JSON.
To send data, organize your data into a python dict and pass this to build_packet. Write the resulting bytearray to the TX characteristic.
