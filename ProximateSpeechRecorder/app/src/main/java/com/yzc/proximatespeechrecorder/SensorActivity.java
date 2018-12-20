package com.yzc.proximatespeechrecorder;

import android.app.Activity;
import android.graphics.Camera;
import android.hardware.Sensor;
import android.hardware.SensorEvent;
import android.hardware.SensorEventListener;
import android.hardware.SensorManager;
import android.media.MediaRecorder;
import android.media.MediaScannerConnection;
import android.os.Bundle;
import android.os.Environment;
import android.os.SystemClock;
import android.util.Log;
import android.view.MotionEvent;
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

    private Long startTimestamp = 0L, startUpTimeMill;
    private Boolean isRecording = false;
    private File file, videoFile;

    private MediaRecorder mRecorder;
    private SensorManager mSensorManager;
    private TextView textView_sensor, textView_touch;
    private Button button_record;
    private int sensorType[] = {
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
    private String sensorName[] = {
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
    private float sensorData[][] = new float[sensorType.length][];

    private final String pathName = Environment.getExternalStorageDirectory().getPath() + "/SensorData/";
    private FileOutputStream fos;

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        setContentView(R.layout.activity_sensor);
        textView_sensor = findViewById(R.id.textView_sensor);
        textView_touch = findViewById(R.id.textView_touch);
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
                //s = Integer.toString(i);
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
        s += " " + Long.toString((sensorEvent.timestamp - startTimestamp) / 1000000L);
        s += " " + Integer.toString(sensorEvent.accuracy);
        for (float data : sensorEvent.values)
            s += " " + Float.toString(data);

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

    @Override
    public boolean dispatchTouchEvent(MotionEvent e) {
        String text = "";
        boolean updated = false;

        for (int i = 0; i < e.getPointerCount(); ++i) {
            int id = e.getPointerId(i);
            int x = (int) e.getX(i), y = (int) e.getY(i);
            float p = e.getPressure(i);
            float s = e.getSize(i);
            text += "Id:" + id + " X:" + x + " Y:" + y;
            text += String.format(Locale.US," S:%.2f P:%.2f", s, p) + "\n";
        }
        if (e.getAction() == MotionEvent.ACTION_UP)
            text = "";
        textView_touch.setText(text);

        if (isRecording) {
            String s = "TOUCH " + e.getAction();
            s += " " + Long.toString((e.getEventTime()- startUpTimeMill));
            s += " " + Integer.toString(e.getPointerCount());
            for(int i = 0; i < e.getPointerCount(); ++i) {
                int id = e.getPointerId(i);
                float x = e.getX(i), y = e.getY(i);
                float p = e.getPressure(i), sz = e.getSize(i);
                s += " " + Integer.toString(id);
                s += " " + Float.toString(x) + " " + Float.toString(y);
                s += " " + Float.toString(p) + " " + Float.toString(sz);
            }
            s += "\n";
            byte [] buffer = s.getBytes();
            try {
                fos.write(buffer);
            } catch (IOException ex) {
                ex.printStackTrace();
            }
        }
        return super.dispatchTouchEvent(e);
    }

    @Override
    public void onClick(View v) {
        switch (v.getId()) {
            case R.id.button_record:
                isRecording ^= true;
                if (isRecording) {
                    button_record.setText("Stop Recording");
                    createDataFile();
                } else {
                    button_record.setText("Start Recording");
                    try {
                        fos.close();
                        mRecorder.stop();
                        mRecorder.reset();
                        mRecorder.release();
                        mRecorder = null;
                    } catch (IOException e) {
                        e.printStackTrace();
                    }
                    MediaScannerConnection.scanFile(this,
                            new String[] { file.getAbsolutePath(), videoFile.getAbsolutePath() }, null, null);
                }
                break;
        }
    }

    private void loadSensor() {
        mSensorManager = (SensorManager) getSystemService(SENSOR_SERVICE);
        if (mSensorManager == null) {
            Log.w("Sensor", "no SENSOR_SERVICE");
            return;
        }

        for (int i = 0; i < sensorType.length; i++) {
            Sensor sensor = mSensorManager.getDefaultSensor(sensorType[i]);
            if (sensor != null) {
                Log.i("loadSensor", "register " + sensorName[i] + " successful");
                mSensorManager.registerListener(this, sensor, SensorManager.SENSOR_DELAY_NORMAL);
            } else
                Log.w("loadSensor", "register " + sensorName[i] + " failed");
        }

        List<Sensor> sensorList = mSensorManager.getSensorList(Sensor.TYPE_ALL);
        for (Sensor sensor : sensorList) {
            Log.d("SensorList", sensor.getName());
        }
    }

    private void createDataFile() {
        try {
            SimpleDateFormat format = new SimpleDateFormat("yy.MM.dd HH_mm_ss", Locale.US);
            String fileName = format.format(new Date());
            File path = new File(pathName);
            file = new File(pathName + fileName + ".txt");
            boolean res;
            if (!path.exists())
                res = path.mkdir();
            if (!file.exists())
                res = file.createNewFile();
            fos = new FileOutputStream(file);

            videoFile = new File(pathName + fileName + ".mp4");
            mRecorder = new MediaRecorder();

            mRecorder.setAudioSource(MediaRecorder.AudioSource.CAMCORDER);
            //mRecorder.setVideoSource(MediaRecorder.VideoSource.CAMERA);

            mRecorder.setOutputFormat(MediaRecorder.OutputFormat.MPEG_4);

            mRecorder.setAudioEncoder(MediaRecorder.AudioEncoder.AMR_NB);
            //mRecorder.setVideoEncoder(MediaRecorder.VideoEncoder.MPEG_4_SP);


            //mRecorder.setVideoSize(640, 480);
            //mRecorder.setVideoFrameRate(30);
            //mRecorder.setVideoEncodingBitRate(3 * 1024 * 1024);
            //mRecorder.setOrientationHint(90);
            mRecorder.setOutputFile(videoFile);
            mRecorder.prepare();
            mRecorder.start();

        } catch (IOException e) {
            e.printStackTrace();
        }

        startTimestamp = SystemClock.elapsedRealtimeNanos();
        startUpTimeMill = SystemClock.uptimeMillis();
        String ss = Long.toString(System.currentTimeMillis()) + "\n";
        ss += Long.toString(startUpTimeMill) + "\n";
        ss += Long.toString(startTimestamp) + "\n";

        for (int i = 0; i < sensorType.length; i++) {
            if (sensorData[i] != null) {
                ss += sensorName[i];
                ss += " 0"; //Timestamp
                ss += " 0"; //Accuracy
                for (float data : sensorData[i])
                    ss += " " + Float.toString(data);
                ss += "\n";
            }
        }
        try {
            fos.write(ss.getBytes());
        } catch (IOException e) {
            e.printStackTrace();
        }
    }
}
