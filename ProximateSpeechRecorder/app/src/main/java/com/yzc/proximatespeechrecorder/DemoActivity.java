package com.yzc.proximatespeechrecorder;

import android.app.Activity;
import android.content.Context;
import android.content.Intent;
import android.content.Loader;
import android.hardware.Sensor;
import android.hardware.SensorEvent;
import android.hardware.SensorEventListener;
import android.hardware.SensorManager;
import android.os.Bundle;
import android.util.Log;
import android.view.View;
import android.widget.Button;
import android.widget.TextView;

import java.io.IOException;
import java.lang.reflect.Array;
import java.util.ArrayList;
import java.util.List;
import java.util.Locale;

public class DemoActivity extends Activity implements SensorEventListener {

    private Context ctx;
    private String TAG = "DemoActivity";
    private TextView textView_sensor;

    private int sensorType[] = SensorUtil.sensorType;
    private String sensorName[] = SensorUtil.sensorName;
    private List<ArrayList<Frame>> data = new ArrayList<>();
    List<Float> a = new ArrayList<>();

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        setContentView(R.layout.activity_demo);
        ctx = this;
        initView();
        loadSensor();
    }

    private void initView() {
        textView_sensor = findViewById(R.id.textView_sensor);
        Button button_calibrate = findViewById(R.id.button_calibrate);
        button_calibrate.setOnClickListener(clickListener);
        for (int i : sensorType)
            data.add(new ArrayList<Frame>());
    }

    View.OnClickListener clickListener = new View.OnClickListener() {
        @Override
        public void onClick(View view) {
            switch (view.getId()) {
                case R.id.button_calibrate:

                    break;
            }
        }
    };

    private void loadSensor() {
        SensorManager mSensorManager = (SensorManager) getSystemService(SENSOR_SERVICE);
        if (mSensorManager == null) {
            Log.w(TAG, "no SENSOR_SERVICE");
            return;
        }

        for (int i = 0; i < sensorType.length; i++) {
            Sensor sensor = mSensorManager.getDefaultSensor(sensorType[i]);
            if (sensor != null) {
                Log.i(TAG, "register " + sensorName[i] + " successful");
                mSensorManager.registerListener(this, sensor, SensorManager.SENSOR_DELAY_GAME);
            } else
                Log.w(TAG, "register " + sensorName[i] + " failed");
        }

    }


    @Override
    public void onSensorChanged(SensorEvent sensorEvent) {
        float[] values = sensorEvent.values;
        StringBuilder sb = new StringBuilder();
        for (int i = 0; i < sensorType.length; i++) {
            ArrayList<Frame> f_list = data.get(i);
            if (sensorEvent.sensor.getType() == sensorType[i]) {
                Frame f = new Frame();
                f.timestamp = sensorEvent.timestamp;
                f.values = values;

                f_list.add(f);
                while(f.timestamp - f_list.get(0).timestamp > 100 * 1000000L)
                    f_list.remove(0);
            }
        }
        textView_sensor.setText(sb.toString());

    }

    private class Frame {
        long timestamp;
        float[] values;
    }

    @Override
    public void onAccuracyChanged(Sensor sensor, int accuracy) {

    }
}
