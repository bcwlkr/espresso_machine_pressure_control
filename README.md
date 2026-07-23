# Espresso machine pressure/flow control
This is a project I developed using the RobotDYN PWM AC dimmer, for my Gemilai G3006 (owl).

This mod *should* work on any espresso machine that uses an AC vibratory pump, such as the ULKA EX5/EP5 or similar 110-220v AC pump.

### Disclosure: build this prject at your own risk, seemingly insignificant things such as connecting incorrect wires to your potentiometer, or running virbatory pumps dry can both start fires and a standard 120v outlet can and WILL kill you if shocked.

#### parts list:
  - RobotDYN - PWM Ac Programmable Light Dimmer https://a.co/d/021D6dAU
  - 14-16awg wire https://a.co/d/083oG2C8
  - 20awg wire (any thin wire for GPIO will work) https://a.co/d/08RyRbat
  - Arduino Nano (any arduino that uses C++ should work, I just like the nano) https://a.co/d/05I2fZrv
      note: If you use an Arduino Nano with the "ATmega328P" AVR microcontroller, you will need the FTDI chip VCP drivers to connect your Nano to Windows 11 (https://ftdichip.com/drivers/vcp-drivers/)
  - spade connectors https://a.co/d/06Q3iqvv
  - B10k Potentiometer https://a.co/d/0h6P61Rn
  - (optional) Arduino Nano screw terminal https://a.co/d/099FGlQE
  - (optional) ABS project box https://a.co/d/0gaIZqGz

  All of these parts are what I used or similar, I suggest using hiogh quality, high temp wire, and components especially if your boiler isn't thermally insulated/shielded. parts marked optional are optional,
but I highly suggest you use all of the parts and any *nice to haves* that you can think of, such as wire ferrules for the screw terminals and mounting brackets, to keep all of your parts from moving in your espresso machine.

## Assembly

### Schematic Reference
<img width="939" height="509" alt="espresso_controller_schematic" src="https://github.com/user-attachments/assets/9f7065a0-929e-4f49-9ede-0cff8c79ffa3" />


### Step 1: Prepare the Enclosure
Because the interior of an espresso machine is a high vibration and high heat environment, standard loose wiring will fail.

Ensure there is a physical air gap and ventilation holes near the dimmer's aluminum heatsink to allow for cooling inside the project box.

Mount the printed enclosure to the internal metal chassis of the espresso machine using machine screws secured with safety wire or blue Loctite to prevent them from backing out under pump vibration.

### Step 2: Wire the Low Voltage Logic
Using the Nano Screw Terminal Shield ensures the GPIO logic wires will not snap from metal fatigue.

Route a wire from the Nano 5V terminal to the Left Pin (Pin 1) of the potentiometer and the VCC pin of the RobotDyn dimmer.

Route a wire from the Nano GND terminal to the Right Pin (Pin 3) of the potentiometer and the GND pin of the RobotDyn dimmer.

Route a wire from the potentiometer Middle Pin (Pin 2) to the Nano A0 terminal.

Route a wire from the Nano D2 terminal to the RobotDyn Z-C (Zero Cross) terminal.

Route a wire from the Nano D3 terminal to the RobotDyn PWM/PSM terminal.

Apply a small bead of hot glue over the screwed down wire terminals to act as a vibration shock absorber.

### Step 3: Flash the Firmware
Connect the Arduino Nano to your PC via USB. Upload the "espresso_controller.ino". This code includes an Exponential Moving Average (EMA) filter to completely smooth out noisy analog readings from the potentiometer. It also features an offline testing timer to output Serial Plotter data without needing live AC voltage.

### Step 4: Test your potentiometer and Arduino (optional but not really)
while connected to your computer of choice, run "monitor.py" to confirm the potentiometer is working properly, when twisting the knob, you should see the raw output and percentage graphs change at the same rate.



