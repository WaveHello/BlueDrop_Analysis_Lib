# import datetime
import numpy as np
from lib.data_classes.BinaryFile import BinaryFile

class pffpFile(BinaryFile):
    # Purpose: To store information and modify a PFFP binary file

    # TODO: Add a time zone category and add that data to the datetime
    def __init__(self, file_dir, calibration_params):
        BinaryFile.__init__(self, file_dir)

        # Store the calibration params fro converting from volts to engineering units
        self.calibration_params = calibration_params
        
        # Get the file name
        self.file_name = self.get_file_name()

        # Get the file drop date
        self.get_file_datetime()

        # Init variables for later storage
        self.num_drops = "Not Checked" 

    def __str__(self):
        # Purpose: Return some information about the file
        return f"File Directory: {self.file_dir} \nNum Drops in file: {self.num_drops} \
        \nDrop Date: {self.datetime.date()} \nDrop Time: {self.datetime.time()} "

    def binary_2_sensor_df(self, size_byte = 3, byte_order = "big", signed = True, acceleration_unit = "g", pressure_unit = "kPa", time_unit = "s"):
        # Purpose read a binary file and transform it to a processed df
        column_names = ["Count", 'Unknown', "2g_accel", "18g_accel", "50g_accel", "pore_pressure", "200g_accel", 
                                                                "55g_x_tilt","55g_y_tilt", "250g_accel"]
        num_columns = len(column_names)

        num_rows = -1

        df = self.binary_file_2_df(column_names, num_columns, num_rows, size_byte, byte_order, signed)

        # Apply the offset to the df
        
        # NOTE: Assumes the columns of the df are IN EXACT ORDER (names can be differnt but values must be the same):
        # [Count, Unknown, 2g_accel, 18g_accel, 50g_accel, pore_pressure, 200g_accel, 55g_x_tilt, 55g_y_tilt, 250g_accel]

        # Drop the count and unknown columns
        columns_2_drop = [0, 1]
        
        columns_header_2_drop = df.columns[columns_2_drop]
        
        # df now has values:
        # [2g_accel, 18g_accel, 50g_accel, pore_pressure, 200g_accel, 55g_x_tilt, 55g_y_tilt, 250g_accel]
        df.drop(columns_header_2_drop, axis = 1, inplace = True)

        # Local variable for the calibration factors
        params = self.calibration_params

        for value in params['Sensor']:
            offset = params[params['Sensor'] == value].iloc[0, 1]
            scale = params[params['Sensor'] == value].iloc[0, 2]

            # Scale the df columns, Formula is (sensor_value + offset)/scale
            df[value] = (df[value] +offset)/scale

        # Get the number of entries in a column
        num_entries = len(df.iloc[:, 0])
        
        # Get the time steps
        time = np.linspace(0, 1, num_entries)
        
        # Store the time in seconds in the df
        df.insert(0, "Time", time)

        # Acceleration scaling
        acceleration_sensor_names = ["2g_accel", "18g_accel", "50g_accel","200g_accel", "55g_x_tilt","55g_y_tilt", "250g_accel"]
        
        df = pffpFile.convert_acceleration_unit(df, acceleration_sensor_names, "g", acceleration_unit)
        
        # Dictionary with conversion from psi to other sets of units
        pressure_conversion_dict = {
                                    "kPa": 6.89476
        }

        if pressure_unit == "psi":
            pass
        elif pressure_unit == "kPa":
            # Convert the pressure to kPa
            df["pore_pressure"] = df["pore_pressure"] * pressure_conversion_dict["kPa"]
        else:
            raise ValueError("Onnly converison from psi to kPa implemented")
        return df
    
    @staticmethod
    def convert_acceleration_unit(df, columns, input_unit, output_unit):
        # Purpose: Convert the acceleration unit from one  to another

        if input_unit  != "g":
            raise IndexError("Conversions starting from units other than g's not implemented")
        
        # Assumes convertion from g's
        acceleration_conversion_dict = {
                                        "m/s^2": 9.80665,
                                        "g": 1
        }

        df[columns] = df[columns] * acceleration_conversion_dict[output_unit]

        return df