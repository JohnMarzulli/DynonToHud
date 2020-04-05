# DynonToHud

Project to take the serial output of a Dynon and make it available as a GDL-90 type service.

sudo python3 setup.py develop pip3 install pyserial

# DynonToHud

## 1\. []()Introduction

This project aims to bring serial data from older Dynon avionics into HUDs and EFBs.

It does this be creating a service that supplies the data in a format based on the Stratux projects `getSituation` format.

**NOTE:** This project has only been tested against a Dynon D180 FlightDek. It is likely to work with other EFIS products made by Dynon with a serial output.

## 2\. []()Intended Usage

This is intended to be used with the StratuxHud(<https://johnmarzulli.github.io/StratuxHud/>) project

## 3\. []()Parts List

You will need a functioning StratuxHud unit.

In this case, having a stand-alone unit (not running on the Stratux) is HIGHLY recommended.

It is also recommended to run the Hud and DynonToHud on a Pi 3B+ to take advantage of the increased processing power and higher frame rates.

- [Serial To USB Adapter](https://www.amazon.com/gp/product/B00IDSM6BW/ref=ppx_yo_dt_b_asin_title_o07_s00?ie=UTF8&psc=1)

A minimum of a single adapter is required for the EFIS data. To allow for EMS data, two adapters are required.

## 4\. []()Recommended Software Install

This software may be included in image files for the StratuxHUD already. Check the (Releases Page)[<https://github.com/JohnMarzulli/StratuxHud/releases>] page.

The easiest way to install is by using a StratuxHud image.

## 5\. []()Development/From Scratch Install instructions

These instructions assume you have the StratuxHud code already running on a Raspberry Pi.

For this installation it is recommended to boot the unit with a full keyboard and an ethernet cable (with internet).

### 5.1\. []()First Boot

1. Wait for the HUD to appear.
2. Press 'Q' on the keyboard to quit to the command line.
3. Verify that the user is 'Pi'
4. `cd ~`
5. `git clone https://github.com/JohnMarzulli/DynonToHud.git`
6. `cd DynonToHud`
7. `sudo python setup.py develop`
8. `crontab -e`
9. Add the following entry to the crontab file:
10. `@reboot python3 /home/pi/DynonToHud/dynon_to_hud.py &`
11. Save and quit.
12. It is suggested to test the code to make sure you have the packages installed and an appropriate version of Python
13. `python3 /home/pi/DynonToHud/dynon_to_hud.py &`
14. The code should start running without returning to the command line. It is expected for it to be unable to read a serial port.
15. You may quite by using ctrl+c
16. `sudo shutdown -h now`

** NOTE: You will need to modify the StratuxHud configuration to point to `localhost:8180`. Please refer to the StratuxHud documentation on how to do this. Without performing this step, the HUD will only draw data from the Stratux unit.

### 5.2\. []()Aircraft Installation

Once the DynonToHud service has been installed and verified to be running, installation into an aircraft is straight forward.

Locate the two nine-pin EFIS and EMS serial cables from the Dynon.

With the aircraft powered off, plug the two USB adapters into the Dynon plugs.

Then plug the two USB ends into the StratuxHud

### 7\. []()Revision History

Date       | Version | Major Changes
---------- | ------- | ----------------
2020-03-?? | Alpha   | Initial release.

## 8\. []()Acknowledgements And Credits

Special thanks to Dynon and Robert Hamilton for the encouragement and support.

## 9\. []()License

This project is covered by the GPL v3 license.

Please see

<license>
</license>
