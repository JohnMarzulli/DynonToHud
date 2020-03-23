import SerialPort from "serialport";

const DefaultDataSource: string = "/dev/ttyUSB0";
const NodeJsSerialPort = require('serialport');
const Readline = require('@serialport/parser-readline');

const port = new NodeJsSerialPort(
    DefaultDataSource,
    {
        baudRate: 115200,
        parity: 'none',
        stopBits: 1,
        dataBits: 8
    });

function sleep(millis: number) {
    return new Promise(resolve => setTimeout(resolve, millis));
}

while (port.opening) {
    sleep(500);
}

if (port.isOpen) {
    const parser = port.pipe(new Readline({ delimiter: '\r\n' }));
    parser.on('data', console.log);
}