package com.yzc.proximatespeechrecorder;

import android.app.Activity;
import android.hardware.Sensor;
import android.hardware.SensorEvent;
import android.hardware.SensorEventListener;
import android.hardware.SensorManager;
import android.media.MediaScannerConnection;
import android.os.Bundle;
import android.os.Environment;
import android.os.SystemClock;
import android.util.Log;
import android.view.View;
import android.widget.Button;
import android.widget.TextView;

import java.io.File;
import java.io.FileOutputStream;
import java.io.IOException;
import java.text.SimpleDateFormat;
import java.util.Date;
import java.util.List;
import java.util.Locale;


public class SensorActivity extends Activity implements SensorEventListener, View.OnClickListener {

    private Long startTimestamp = 0L;
    private Boolean isRecording = false;

    private SensorManager mSensorManager;
    private TextView textView_sensor;
    private Button button_record;
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

    private final String pathName = Environment.getExternalStorageDirectory().getPath() + "/SensorData/";
    private FileOutputStream fos;

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        setContentView(R.layout.activity_sensor);
        textView_sensor = findViewById(R.id.textView_sensor);
        button_record = findViewById(R.id.button_record);
        button_record.setOnClickListener(this);
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
        String s = "";
        StringBuilder sb = new StringBuilder();
        for (int i = 0; i < sensorType.length; i++) {
            if (sensorEvent.sensor.getType() == sensorType[i]) {
                sensorData[i] = values;
                s = sensorName[i];
            }

            if (sensorData[i] != null) {
                sb.append(sensorName[i]);
                for (float data : sensorData[i])
                    sb.append(String.format(Locale.US, " %.2f", data));
                sb.append("\n");
            }
        }
        textView_sensor.setText(sb.toString());
        if (!isRecording)
            return;
        if (startTimestamp == 0) {
            startTimestamp = sensorEvent.timestamp;
            String ss = Long.toString(System.currentTimeMillis()) + "\n";
            ss += Long.toString(SystemClock.elapsedRealtimeNanos()) + "\n";
            try {
                fos.write(ss.getBytes());
            } catch (IOException e) {
                // TODO Auto-generated catch block
                e.printStackTrace();
            }
        }
        s += " " + Long.toString((sensorEvent.timestamp - startTimestamp) / 1000000);
        s += " " + Integer.toString(sensorEvent.accuracy);
        for (int i=0; i < sensorEvent.values.length; ++i)
            s += " " + Float.toString(sensorEvent.values[i]);
        s += "\n";
        byte [] buffer = s.getBytes();
        try {
            fos.write(buffer);
        } catch (IOException e) {
            e.printStackTrace();
        }
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
            Sensor sensor = mSensorManager.getDefaultSensor(type);
            mSensorManager.registerListener(this, sensor, SensorManager.SENSOR_DELAY_NORMAL);
        }

        List<Sensor> sensorList = mSensorManager.getSensorList(Sensor.TYPE_ALL);
        for (Sensor sensor : sensorList) {
            Log.d("SensorList", sensor.getName());
        }
    }
    @Override
    public void onClick(View v) {
        switch (v.getId()) {
            case R.id.button_record:
                isRecording ^= true;
                if (isRecording) {
                    button_record.setText("Stop Recording");
                    try {
                        SimpleDateFormat format = new SimpleDateFormat("yy.MM.dd HH_mm_ss", Locale.US);
                        String fileName = format.format(new Date()) + ".txt";
                        File path = new File(pathName);
                        File file = new File(pathName + fileName);
                        boolean res;
                        if (!path.exists())
                            res = path.mkdir();
                        if (!file.exists())
                            res = file.createNewFile();
                        fos = new FileOutputStream(file);
                        MediaScannerConnection.scanFile(this, new String[] { file.getAbsolutePath() }, null, null);
                    } catch (IOException e) {
                        e.printStackTrace();
                    }
                } else {
                    button_record.setText("Start Recording");
                    startTimestamp = 0L;
                    try {
                        fos.close();
                    } catch (IOException e) {
                        e.printStackTrace();
                    }
                }
                break;
        }
    }
}
