# Espresso machine pressure/flow control
This is a project I developed using the RobotDYN PWM AC dimmer, for my Gemilai G3006 (owl).

This mod *should* work on any espresso machine that uses an AC vibratory pump, such as the ULKA EX5/EP5 or similar 110-220v AC pump.

parts list:
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

