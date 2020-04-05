import datetime
import threading

METERS_TO_YARDS = 1.09361
AIRSPEED_CONVERSION_FACTOR = 0.647

class EfisAndEmsDecoder(object):
    # Based on
    # https://www.dynonavionics.com/includes/guides/FlightDEK-D180_Pilot's_User_Guide_Rev_H.pdf

    def __init__(
        self
    ):
        super().__init__()

        self.efis_last_updated = None
        self.seconds_since_last_update = 10000

        self.ahrs_package = {}

        self.max_lateral_gs = 1.0
        self.min_lateral_gs = 1.0

        self.max_vertical_gs = 1.0
        self.min_vertical_gs = 1.0

        self.__lock__ = threading.Lock()

    def __get_data_length__(
        self,
        serial_data: str
    ) -> int:
        return 0 if serial_data is None else len(serial_data)

    def update_gs(
        self,
        current_vertical_gs: float,
        current_lateral_gs: float
    ):
        if current_vertical_gs < self.min_vertical_gs:
            self.min_vertical_gs = current_vertical_gs

        if current_vertical_gs > self.max_vertical_gs:
            self.max_vertical_gs = current_vertical_gs

        if current_lateral_gs < self.min_lateral_gs:
            self.min_lateral_gs = current_lateral_gs

        if current_lateral_gs > self.max_lateral_gs:
            self.max_lateral_gs = current_lateral_gs

    def get_gs_to_report(
        self,
        current_vertical_gs: float,
        current_lateral_gs: float
    ) -> float:
        if abs(current_lateral_gs) > abs(current_vertical_gs):
            return current_lateral_gs

        return current_vertical_gs

    def efis_updated(
        self
    ) -> int:
        seconds_since_update = 0
        new_update_time = datetime.datetime.utcnow()

        if self.efis_last_updated is None:
            seconds_since_update = 10000
        else:
            seconds_since_update = (
                new_update_time - self.efis_last_updated).seconds

        self.efis_last_updated = new_update_time
        self.seconds_since_last_update = seconds_since_update

        return seconds_since_update

    def decode_efis(
        self,
        serial_data: str
    ) -> dict:
        # Example:
        # "21301133-008+00001100000+0024-002-00+1099FC39FE01AC"

        if self.__get_data_length__(serial_data) != 53:
            return {} if self.seconds_since_last_update > .5 else self.ahrs_package

        hour = serial_data[0:2]
        minute = serial_data[2:4]
        second = serial_data[4:6]
        time_fraction = str(float(serial_data[6:8]) / 64.0)[2:4]
        pitch = float(serial_data[8:12]) / 10.0
        roll = float(serial_data[12:17]) / 10.0
        yaw = int(serial_data[17:20])
        ias_meters_per_second = (float(serial_data[20:24]) / 10.0)
        airspeed = ias_meters_per_second * AIRSPEED_CONVERSION_FACTOR
        # pres or displayed
        altitude = METERS_TO_YARDS * float(serial_data[24:29])
        turn_rate_or_vsi = float(serial_data[29:33]) / 10.0
        # lateral_gs = float(serial_data[33:36]) / 100.0
        vertical_gs = float(serial_data[36:39]) / 10.0
        # percentage to stall 0 to 99
        angle_of_attack = int(serial_data[39:41])
        status_bitmask = int(serial_data[41:47], 16)

        is_pressure_alt_and_vsi = ((status_bitmask & 1) == 1)

        current_time = datetime.datetime.utcnow()
        last_time_received = "{0:04}-{1:02}-{2:02}T{3}:{4}:{5}.{6}Z".format(
            current_time.year,
            current_time.month,
            current_time.day,
            hour,
            minute,
            second,
            time_fraction
        )

        decoded_efis = {
            "GPSTime": last_time_received,
            "GPSLastGPSTimeStratuxTime": last_time_received,
            "BaroLastMeasurementTime": last_time_received,
            # Degrees. 3276.7 = Invalid.
            "AHRSPitch": pitch,
            # Degrees. 3276.7 = Invalid.
            "AHRSRoll": roll,
            # Degrees. Process mod 360. 3276.7 = Invalid.
            "AHRSGyroHeading": yaw,
            # Degrees. Process mod 360. 3276.7 = Invalid.
            "AHRSMagHeading": yaw,
            # Current G load, in G's. Reads 1 G at rest.
            "AHRSGLoad": vertical_gs,
            # Minimum recorded G load, in G's.
            "AHRSGLoadMin": self.min_vertical_gs,
            # Maximum recorded G load, in G's.
            "AHRSGLoadMax": self.max_vertical_gs,
            # Stratux clock ticks since last attitude update. Reference against /getStatus -> UptimeClock.
            "AHRSLastAttitudeTime": last_time_received,
            "AHRSAirspeed": airspeed,
            "AHRSAOA": angle_of_attack,
            "AHRSStatus": 7
        }

        if is_pressure_alt_and_vsi:
            decoded_efis["BaroPressureAltitude"] = altitude * METERS_TO_YARDS
            decoded_efis["BaroVerticalSpeed"] = METERS_TO_YARDS * \
                turn_rate_or_vsi
        else:
            decoded_efis["Altitude"] = altitude * METERS_TO_YARDS
            decoded_efis["AHRSTurnRate"] = turn_rate_or_vsi

        self.__lock__.acquire()
        self.ahrs_package.update(decoded_efis)
        self.__lock__.release()

        self.efis_updated()

        return self.ahrs_package

    def decode_ems(
        self,
        serial_data: str
    ) -> dict:
        # Example:
        # 211316033190079023001119-020000000000066059CHT00092CHT00090N/AXXXXX099900840084058705270690116109209047124022135111036A
        if self.__get_data_length__(serial_data) != 121:
            return {} if self.seconds_since_last_update > .5 else self.ahrs_package

        # hour = serial_data[0:2]
        # minute = serial_data[2:4]
        # second = serial_data[4:6]
        # time_fraction = str(float(serial_data[6:8]) / 64.0)[2:4]
        manifold_pressure = float(serial_data[8:12]) / 100.0
        oil_temp = serial_data[12:15]
        oil_pressure = float(serial_data[15:18]) / 10.0
        fuel_pressure = float(serial_data[18:21]) / 10.0
        volts = float(serial_data[21:24]) / 10.0
        amps = serial_data[24:27]
        rpm = float(serial_data[27:30]) * 10.0
        # fuel_flow = float(serial_data[30:33]) / 10.0
        # gallons_remaining = float(serial_data[33:37]) / 10.0
        fuel_level_1 = float(serial_data[37:40]) / 10.0
        fuel_level_2 = float(serial_data[40:43]) / 10.0
        gp_1 = serial_data[43:51]
        gp_2 = serial_data[51:59]
        # gp_3 = serial_data[59:67]
        # gp_thermo = serial_data[67:71]
        # egt_1 = int(serial_data[71:75])
        # egt_2 = int(serial_data[75:79])
        # egt_3 = int(serial_data[79:83])
        # egt_4 = int(serial_data[83:87])
        # egt_5 = int(serial_data[87:91])
        # egt_6 = int(serial_data[91:95])
        # cht_1 = int(serial_data[95:98])
        # cht_2 = int(serial_data[98:101])
        # cht_3 = int(serial_data[101:104])
        # cht_4 = int(serial_data[104:107])
        # cht_5 = int(serial_data[107:110])
        # cht_6 = int(serial_data[110:113])
        # contact_1 = serial_data[113:114]
        # contact_2 = serial_data[114:115]
        # product = serial_data[115:117]

        ems_package = {
            'EmsMap': manifold_pressure,
            'EmsOilTemp': oil_temp,
            'EmsOilPressure': oil_pressure,
            'EmsFuelPressure': fuel_pressure,
            'EmsVolts': volts,
            'EmsAmps': amps,
            'EmsRpm': rpm,
            'EmsFuelLevel1': fuel_level_1,
            'EmsFuelLevel2': fuel_level_2,
            'EmsGp1': gp_1,
            'EmsGp2': gp_2
        }

        self.__lock__.acquire()
        self.ahrs_package.update(ems_package)
        self.__lock__.release()

        return self.ahrs_package

    def get_ahrs_package(
        self
    ) -> dict:
        """
        Returns a thread-safe copy of the current AHRS package.
        """

        cloned_package = {'Service': 'DynonToHud'}
        self.__lock__.acquire()
        cloned_package.update(self.ahrs_package)
        self.__lock__.release()

        return cloned_package


if __name__ == '__main__':
    decoder = EfisAndEmsDecoder()

    decoder.decode_efis(
        "21301133-008+00001100000+0024-002-00+1099FC39FE01AC\r\n")
    decoder.decode_ems(
        "211316033190079023001119-020000000000066059CHT00092CHT00090N/AXXXXX099900840084058705270690116109209047124022135111036A\r\n")
