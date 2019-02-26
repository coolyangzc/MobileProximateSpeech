package com.yzc.proximatespeechrecorder;

import android.hardware.Sensor;

public class SensorUtil {

    public static final int sensorType[] = {
            Sensor.TYPE_ACCELEROMETER, Sensor.TYPE_MAGNETIC_FIELD,
            Sensor.TYPE_GYROSCOPE, Sensor.TYPE_ROTATION_VECTOR,
            Sensor.TYPE_GRAVITY, Sensor.TYPE_PROXIMITY,
            Sensor.TYPE_LIGHT, Sensor.TYPE_LINEAR_ACCELERATION,

            Sensor.TYPE_ACCELEROMETER_UNCALIBRATED, Sensor.TYPE_PRESSURE,
            Sensor.TYPE_RELATIVE_HUMIDITY, Sensor.TYPE_AMBIENT_TEMPERATURE,

            Sensor.TYPE_MAGNETIC_FIELD_UNCALIBRATED, Sensor.TYPE_GAME_ROTATION_VECTOR,
            Sensor.TYPE_GYROSCOPE_UNCALIBRATED, Sensor.TYPE_SIGNIFICANT_MOTION,
            Sensor.TYPE_STEP_DETECTOR, Sensor.TYPE_STEP_COUNTER
    };

    public static final String sensorName[] = {
            "ACCELEROMETER", "MAGNETIC_FIELD",
            "GYROSCOPE", "ROTATION_VECTOR",
            "GRAVITY", "PROXIMITY",
            "LIGHT", "LINEAR_ACCELERATION",

            "ACCELEROMETER_UNCALIBRATED", "PRESSURE",
            "RELATIVE_HUMIDITY", "AMBIENT_TEMPERATURE",

            "MAGNETIC_FIELD_UNCALIBRATED", "GAME_ROTATION_VECTOR",
            "GYROSCOPE_UNCALIBRATED", "SIGNIFICANT_MOTION",
            "STEP_DETECTOR", "STEP_COUNTER"
    };

    public static final int sensorNum = sensorName.length;

    public static int getSensorID(String name) {
        for (int i = 0; i < sensorName.length; ++i)
            if (name.equals(sensorName[i]))
                return i;
        return -1;
    }

}
