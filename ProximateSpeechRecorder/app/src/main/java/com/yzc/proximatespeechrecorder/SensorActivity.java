package com.yzc.proximatespeechrecorder;

import android.app.Activity;
import android.hardware.Sensor;
import android.hardware.SensorEvent;
import android.hardware.SensorEventListener;
import android.hardware.SensorManager;
import android.os.Bundle;
import android.util.Log;
import android.widget.TextView;

import java.util.ArrayList;
import java.util.List;
import java.util.Locale;


public class SensorActivity extends Activity implements SensorEventListener {

    private SensorManager mSensorManager;
    private Sensor sensor;
    private TextView textView_sensor;
    private int sensorType[] = {
            Sensor.TYPE_ACCELEROMETER, Sensor.TYPE_ROTATION_VECTOR,
            Sensor.TYPE_GYROSCOPE, Sensor.TYPE_MAGNETIC_FIELD,
            Sensor.TYPE_GRAVITY, Sensor.TYPE_PROXIMITY,
            Sensor.TYPE_LIGHT, Sensor.TYPE_LINEAR_ACCELERATION
    };
    private String sensorName[] = {
            "ACCELEROMETER", "ROTATION_VECTOR",
            "GYROSCOPE", "MAGNETIC_FIELD",
            "GRAVITY", "PROXIMITY",
            "LIGHT", "LINEAR_ACCELERATION",
    };
    private float sensorData[][] = new float[sensorType.length][];

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        setContentView(R.layout.activity_sensor);
        textView_sensor = findViewById(R.id.textView_sensor);
        loadSensor();
    }

    @Override
    protected void onResume() {
        super.onResume();
        //mSensorManager.registerListener(this, mAccelerometer, SensorManager.SENSOR_DELAY_NORMAL);
        //mSensorManager.registerListener(this, mRotationVector, SensorManager.SENSOR_DELAY_NORMAL);
    }

    @Override
    protected void onPause() {
        super.onPause();
        //mSensorManager.unregisterListener(this);
    }

    @Override
    public void onSensorChanged(SensorEvent sensorEvent) {
        float[] values = sensorEvent.values;
        StringBuilder sb = new StringBuilder();
        for (int i = 0; i < sensorType.length; i++) {
            if (sensorEvent.sensor.getType() == sensorType[i])
                sensorData[i] = values;
            if (sensorData[i] != null) {
                sb.append(sensorName[i]);
                for (float data : sensorData[i])
                    sb.append(String.format(Locale.US, " %.2f", data));
                sb.append("\n");
            }
        }
        textView_sensor.setText(sb.toString());
    }

    @Override
    public void onAccuracyChanged(Sensor sensor, int accuracy) {

    }

    private void loadSensor() {
        mSensorManager = (SensorManager) getSystemService(SENSOR_SERVICE);
        if (mSensorManager == null) {
            Log.w("Sensor", "no SENSOR_SERVICE");
            return;
        }

        for(int type:sensorType) {
            sensor = mSensorManager.getDefaultSensor(type);
            mSensorManager.registerListener(this, sensor, SensorManager.SENSOR_DELAY_NORMAL);
        }
        List<Sensor> sensorList = mSensorManager.getSensorList(Sensor.TYPE_ALL);
        for (Sensor sensor : sensorList) {
            Log.d("SensorList", sensor.getName());
        }
    }
}
