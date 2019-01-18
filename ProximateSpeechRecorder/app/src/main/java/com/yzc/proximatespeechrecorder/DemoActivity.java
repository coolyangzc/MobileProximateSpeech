package com.yzc.proximatespeechrecorder;

import android.app.Activity;
import android.content.Context;
import android.hardware.Sensor;
import android.hardware.SensorEvent;
import android.hardware.SensorEventListener;
import android.hardware.SensorManager;
import android.os.Bundle;
import android.os.VibrationEffect;
import android.os.Vibrator;
import android.util.Log;
import android.view.View;
import android.widget.Button;
import android.widget.TextView;

import java.util.ArrayList;
import java.util.List;
import java.util.Locale;

public class DemoActivity extends Activity implements SensorEventListener {

    private Context ctx;
    private String TAG = "DemoActivity";
    private TextView textView_sensor;
    private Vibrator mVibrator;

    private int sensorType[] = SensorUtil.sensorType;
    private String sensorName[] = SensorUtil.sensorName;
    private List<ArrayList<Frame>> data = new ArrayList<>();
    private Frame dataOffset[] = new Frame[SensorUtil.sensorNum];
    private long successTimestamp, triggerTimestamp;

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

        for (int i = 0; i < SensorUtil.sensorNum; ++i) {
            data.add(new ArrayList<Frame>());
            dataOffset[i] = new Frame();
        }
    }

    View.OnClickListener clickListener = new View.OnClickListener() {
        @Override
        public void onClick(View view) {
            switch (view.getId()) {
                case R.id.button_calibrate:
                    int id = SensorUtil.getSensorID("LINEAR_ACCELERATION");
                    float copyValues[] = data.get(id).get(data.get(id).size() - 1).values;
                    dataOffset[id].values = copyValues.clone();

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

        mVibrator = (Vibrator)getApplication().getSystemService(VIBRATOR_SERVICE);

    }


    @Override
    public void onSensorChanged(SensorEvent sensorEvent) {
        float[] values = sensorEvent.values;
        int type = sensorEvent.sensor.getType();
        for (int i = 0; i < sensorType.length; ++i) {
            ArrayList<Frame> f_list = data.get(i);
            if (type == sensorType[i]) {
                Frame f = new Frame();
                f.timestamp = sensorEvent.timestamp;
                f.values = values;
                f_list.add(f);
                while(f.timestamp - f_list.get(0).timestamp > 1000 * 1000000L)
                    f_list.remove(0);
            }
        }
        if (type == Sensor.TYPE_LINEAR_ACCELERATION) {
            boolean res = check_LINEAR_ACCELERATION();
            if (res)
                successTimestamp = sensorEvent.timestamp;

            Frame f_proximity = getBack("PROXIMITY");
            textView_sensor.setText(String.valueOf(f_proximity.values[2]));
            if (sensorEvent.timestamp - triggerTimestamp <= 500 * 1000000L)
                return;
            if (f_proximity.values[2] > 0 && sensorEvent.timestamp - successTimestamp <= 300 * 1000000L) {
                VibrationEffect ve = VibrationEffect.createOneShot(100, 1);
                mVibrator.vibrate(ve);
                triggerTimestamp = sensorEvent.timestamp;
            }
        }

    }

    private boolean check_LINEAR_ACCELERATION() {
        StringBuilder sb = new StringBuilder();
        int id = SensorUtil.getSensorID("LINEAR_ACCELERATION");
        ArrayList<Frame> f_list = data.get(id);
        float t = f_list.get(f_list.size() - 1).timestamp;
        float sum[] = new float[3];
        for (Frame f: f_list) {
            if (t - f.timestamp > 200 * 1000000L)
                continue;
            float v[] = f.values.clone();
            for (int j = 0; j < dataOffset[id].values.length; ++j)
                v[j] -= dataOffset[id].values[j];
            for (int i = 0; i < v.length; ++i)
                sum[i] += v[i];
        }
        boolean rapid = false;
        for(int i = 0; i < 3; ++i)
            if (Math.abs(sum[i]) > 30)
                rapid = true;
        if (rapid)
            sb.append("Rapid!!!!\n");
        sb.append(String.format(Locale.US, " %.1f",
                Math.abs(sum[0]) + Math.abs(sum[1]) + Math.abs(sum[2])));
        for (int i = 0; i < 3; ++i)
            sb.append(String.format(Locale.US, " %.1f", Math.abs(sum[i])));

        //textView_sensor.setText(sb.toString());
        return rapid;
    }

    private Frame getBack(String name) {
        int id = SensorUtil.getSensorID(name);
        return data.get(id).get(data.get(id).size() - 1);
    }
    private class Frame {
        long timestamp;
        float[] values = new float[0];
    }

    @Override
    public void onAccuracyChanged(Sensor sensor, int accuracy) {

    }
}
