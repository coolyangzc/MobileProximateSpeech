package com.yzc.proximatespeechrecorder;

import android.Manifest;
import android.app.Activity;
import android.app.AlertDialog;
import android.content.Context;
import android.content.DialogInterface;
import android.content.Intent;
import android.content.pm.PackageManager;
import android.graphics.Color;
import android.hardware.Sensor;
import android.hardware.SensorEvent;
import android.hardware.SensorEventListener;
import android.hardware.SensorManager;
import android.hardware.camera2.CameraAccessException;
import android.hardware.camera2.CameraCaptureSession;
import android.hardware.camera2.CameraDevice;
import android.hardware.camera2.CameraManager;
import android.hardware.camera2.CaptureRequest;
import android.media.CamcorderProfile;
import android.media.MediaRecorder;
import android.media.MediaScannerConnection;
import android.os.Bundle;
import android.os.Environment;
import android.os.SystemClock;
import android.os.VibrationEffect;
import android.os.Vibrator;
import android.support.v4.app.ActivityCompat;
import android.text.InputType;
import android.util.Log;
import android.view.KeyEvent;
import android.view.MotionEvent;
import android.view.Surface;
import android.view.View;
import android.widget.Button;
import android.widget.EditText;
import android.widget.TextView;
import android.widget.Toast;

import java.io.File;
import java.io.FileOutputStream;
import java.io.IOException;
import java.text.SimpleDateFormat;
import java.util.ArrayList;
import java.util.Date;
import java.util.List;
import java.util.Locale;

public class Study1Activity extends Activity implements SensorEventListener {

    private Long startTimestamp, startUpTimeMillis, startTimeMillis;
    private Boolean isRecording = false;
    private File file, videoFile;
    private Context ctx;
    private String TAG = "ProximateSpeechRecorder";

    //Camera2
    private String mCameraIdFront;
    private CameraDevice mCameraDevice;
    private MediaRecorder mMediaRecorder;
    private CaptureRequest.Builder mCaptureBuilder;
    private CaptureRequest mCaptureRequest;
    private CameraCaptureSession mCaptureSession;

    private SensorManager mSensorManager;
    private Vibrator mVibrator;
    private Button button_record, button_goto, button_redo;
    private TextView textView_description;

    private int sensorType[] = SensorUtil.sensorType;
    private String sensorName[] = SensorUtil.sensorName;
    private float sensorData[][] = new float[sensorType.length][];

    private final String pathName =
            Environment.getExternalStorageDirectory().getPath() +
                    "/SensorData/Study1/";
    private FileOutputStream fos;

    private Study1Task tasks;

    static {
        System.loadLibrary("native-lib");
    }

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        setContentView(R.layout.activity_study1);
        ctx = this;
        Intent intent = getIntent();
        int seed = intent.getIntExtra("randomSeed", 0);
        tasks = new Study1Task(seed);
        initViews();
        loadSensor();
        setupCamera();
        openCamera(mCameraIdFront);
        mVibrator = (Vibrator)getApplication().getSystemService(VIBRATOR_SERVICE);
    }

    private void initViews() {
        textView_description = findViewById(R.id.textView_recv);
        textView_description.setText(tasks.getTaskDescription());
        button_record = findViewById(R.id.button_record);
        button_record.setOnClickListener(clickListener);
        button_goto = findViewById(R.id.button_goto);
        button_goto.setOnLongClickListener(longClickListener);
        button_redo = findViewById(R.id.button_redo);
        button_redo.setOnLongClickListener(longClickListener);
    }

    View.OnClickListener clickListener = new View.OnClickListener() {
        @Override
        public void onClick(View view) {
            switch (view.getId()) {
                case R.id.button_record:
                    isRecording ^= true;
                    changeButtonText(isRecording);
                    if (isRecording) {
                        createDataFile();
                        prepareMediaRecorder();
                        startMediaRecorder();
                        readDiffStart();
                    } else {
                        try {
                            fos.close();
                        } catch (IOException e) {
                            e.printStackTrace();
                        }
                        stopMediaRecorder();
                        readDiffStop();
                        MediaScannerConnection.scanFile(ctx,
                                new String[] { file.getAbsolutePath(), videoFile.getAbsolutePath() },
                                null, null);
                        textView_description.setText(tasks.nextTask());
                        long[] timings = {0, 100};
                        VibrationEffect ve = VibrationEffect.createWaveform(timings, -1);
                        mVibrator.vibrate(ve);
                    }
                    break;
            }
        }
    };

    private void changeButtonText(boolean startRecording) {
        if (startRecording) {
            button_record.setText("结束");
            button_record.setTextColor(Color.RED);
            button_goto.setText("");
            button_redo.setText("");
        } else {
            button_record.setText("开始");
            button_record.setTextColor(Color.BLACK);
            button_goto.setText("跳转");
            button_redo.setText("重做");
        }
    }

    View.OnLongClickListener longClickListener = new View.OnLongClickListener() {

        @Override
        public boolean onLongClick(View v) {
            if (isRecording)
                return false;
            switch (v.getId()) {
                case R.id.button_goto:
                    AlertDialog.Builder builder = new AlertDialog.Builder(ctx);
                    builder.setTitle("跳转至");
                    final EditText et = new EditText(ctx);
                    et.setInputType(InputType.TYPE_CLASS_NUMBER);
                    builder.setView(et);
                    builder.setPositiveButton("是", new DialogInterface.OnClickListener() {
                        @Override
                        public void onClick(DialogInterface dialog, int which) {
                            tasks.changeTaskId(Integer.valueOf(et.getText().toString()));
                            textView_description.setText(tasks.getTaskDescription());
                        }
                    });
                    builder.setNegativeButton("否", null);
                    builder.show();
                    break;
                case R.id.button_redo:
                    textView_description.setText(tasks.prevTask());
                    break;
            }
            return false;
        }
    };

    @Override
    public void onSensorChanged(SensorEvent sensorEvent) {
        float[] values = sensorEvent.values;
        String s = "";
        for (int i = 0; i < sensorType.length; i++) {
            if (sensorEvent.sensor.getType() == sensorType[i]) {
                sensorData[i] = values;
                s = sensorName[i];
                break;
            }
        }
        if (sensorEvent.sensor.getType() == Sensor.TYPE_LINEAR_ACCELERATION)
            Log.d(TAG, Long.toString(sensorEvent.timestamp / 1000000L));
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
        if (isRecording) {
            String s = "TOUCH";
            s += " " + Long.toString((e.getEventTime() - startUpTimeMillis));
            s += " -1"; //Accuracy
            s += " " + e.getAction();
            s += " " + Float.toString(e.getRawX()) + " " + Float.toString(e.getRawY());

            s += " " + Integer.toString(e.getPointerCount());
            for(int i = 0; i < e.getPointerCount(); ++i) {
                s += " " + Integer.toString(e.getPointerId(i));
                List<Float> touchData = new ArrayList<Float>();
                touchData.add(e.getX(i));
                touchData.add(e.getY(i));
                touchData.add(e.getPressure(i));
                touchData.add(e.getSize(i));
                touchData.add(e.getOrientation(i));
                touchData.add(e.getTouchMajor(i)); touchData.add(e.getTouchMinor(i));
                touchData.add(e.getToolMajor(i)); touchData.add(e.getToolMinor(i));

                for (Float data : touchData)
                    s += " " + data.toString();
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
                mSensorManager.registerListener(this, sensor, SensorManager.SENSOR_DELAY_GAME);
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
            SimpleDateFormat format = new SimpleDateFormat("yyMMdd HH_mm_ss", Locale.US);
            String fileName = format.format(new Date());
            String curPathName = pathName +
                    new SimpleDateFormat("yyMMdd", Locale.US).format(new Date()) + "/";
            File path = new File(curPathName);
            file = new File(curPathName + fileName + ".txt");
            boolean res;
            if (!path.exists())
                res = path.mkdir();
            if (!file.exists())
                res = file.createNewFile();
            fos = new FileOutputStream(file);
            videoFile = new File(curPathName + fileName + ".mp4");
        } catch (IOException e) {
            e.printStackTrace();
        }
        String ss = tasks.getTaskDescription();
        startTimeMillis = System.currentTimeMillis();
        startUpTimeMillis = SystemClock.uptimeMillis();
        startTimestamp = SystemClock.elapsedRealtimeNanos();
        ss += Long.toString(startTimeMillis) + "\n";
        ss += Long.toString(startUpTimeMillis) + "\n";
        ss += Long.toString(startTimestamp) + "\n";

        for (int i = 0; i < sensorType.length; i++) {
            if (sensorData[i] != null) {
                ss += sensorName[i];
                ss += " 0"; //Timestamp
                ss += " -1"; //Accuracy
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

    /**
     * *************************************Capacity************************************************
     */

    public void processCapa(short[] data, long timestamp){
        if (isRecording) {
            String s = "CAPACITY";
            s += " " + Long.toString(timestamp - startTimeMillis);
            s += " -1"; //Accuracy
            for (short c : data)
                s += " " + Short.toString(c);
            s += "\n";
            try {
                fos.write(s.getBytes());
            } catch (IOException e) {
                e.printStackTrace();
            }
        }
    }
    /**
     * A native method that is implemented by the 'native-lib' native library,
     * which is packaged with this application.
     */
    public native void readDiffStart();
    public native void readDiffStop(); // Java_com_example_diffshow_MainActivity_readDiffStop


    /**
     * *************************************Camera2*************************************************
     */
    private void setupCamera() {
        try {
            CameraManager manager = (CameraManager) getSystemService(Context.CAMERA_SERVICE);
            if (manager != null)
                mCameraIdFront = manager.getCameraIdList()[1];
            else
                Log.d(TAG, "getSystemService failed");
            mMediaRecorder = new MediaRecorder();
        } catch (Exception e) {
            e.printStackTrace();
        }
    }

    private void openCamera(String CameraId) {
        CameraManager manager = (CameraManager) getSystemService(Context.CAMERA_SERVICE);
        try {
            if (ActivityCompat.checkSelfPermission(
                    this, Manifest.permission.CAMERA) != PackageManager.PERMISSION_GRANTED) {
                return;
            }
            manager.openCamera(CameraId, mStateCallback, null);
        } catch (CameraAccessException e) {
            e.printStackTrace();
        }
    }

    private CameraDevice.StateCallback mStateCallback = new CameraDevice.StateCallback() {
        @Override
        public void onOpened(CameraDevice camera) {
            Log.d(TAG, "onOpened");
            mCameraDevice = camera;
        }

        @Override
        public void onDisconnected(CameraDevice cameraDevice) {
            cameraDevice.close();
            mCameraDevice = null;
        }

        @Override
        public void onError(CameraDevice cameraDevice, int error) {
            cameraDevice.close();
            mCameraDevice = null;
        }
    };

    private void prepareMediaRecorder() {
        try {
            Log.d(TAG, "prepareMediaRecorder");
            setupMediaRecorder();

            mCaptureBuilder = mCameraDevice.createCaptureRequest(CameraDevice.TEMPLATE_RECORD);
            List<Surface> surfaces = new ArrayList<>();

            Surface recorderSurface = mMediaRecorder.getSurface();
            surfaces.add(recorderSurface);
            mCaptureBuilder.addTarget(recorderSurface);


            mCameraDevice.createCaptureSession(surfaces, new CameraCaptureSession.StateCallback() {
                @Override
                public void onConfigured(CameraCaptureSession session) {
                    try {
                        mCaptureRequest = mCaptureBuilder.build();
                        mCaptureSession = session;
                        mCaptureSession.setRepeatingRequest(mCaptureRequest, null, null);
                    } catch (Exception e) {
                        e.printStackTrace();
                    }
                }

                @Override
                public void onConfigureFailed(CameraCaptureSession session) {
                    Log.d(TAG, "onConfigureFailed");
                }
            }, null);
        } catch (Exception e) {
            e.printStackTrace();
        }
    }

    private void startMediaRecorder() {
        Log.d(TAG, "startMediaRecorder");
        try {
            mMediaRecorder.start();
        } catch (Exception e) {
            e.printStackTrace();
        }
    }

    private void stopMediaRecorder() {
        try {
            mMediaRecorder.stop();
            mMediaRecorder.reset();
            resetCamera();
        } catch (Exception e) {
            Toast.makeText(this, "录制时间过短", Toast.LENGTH_LONG).show();
            resetCamera();
        }
    }

    public void resetCamera() {
        if (mCameraDevice != null) {
            mCameraDevice.close();
        }
        setupCamera();
        openCamera(mCameraIdFront);
    }

    private void setupMediaRecorder() {
        try {
            Log.d(TAG, "setupMediaRecorder");
            mMediaRecorder.reset();
            mMediaRecorder.setAudioSource(MediaRecorder.AudioSource.MIC);
            mMediaRecorder.setAudioChannels(2);
            mMediaRecorder.setAudioSamplingRate(44100);
            mMediaRecorder.setAudioEncodingBitRate(16 * 44100);
            mMediaRecorder.setVideoSource(MediaRecorder.VideoSource.SURFACE);
            if (CamcorderProfile.hasProfile(CamcorderProfile.QUALITY_1080P)) {
                CamcorderProfile profile = CamcorderProfile.get(CamcorderProfile.QUALITY_1080P);
                //profile.videoBitRate = 8 * 1920 * 1080;
                //profile.videoCodec = MediaRecorder.VideoEncoder.H264;
                profile.audioCodec = MediaRecorder.AudioEncoder.AAC;
                profile.audioChannels = 2;
                profile.audioSampleRate = 44100;
                profile.audioBitRate = 16 * 44100;
                mMediaRecorder.setProfile(profile);
            }
            //mMediaRecorder.setAudioEncoder(MediaRecorder.AudioEncoder.AAC);
            mMediaRecorder.setOutputFile(videoFile);
            mMediaRecorder.setOrientationHint(270);
            mMediaRecorder.prepare();
        } catch (Exception e) {
            e.printStackTrace();
        }
    }

    @Override
    public boolean onKeyDown(int keyCode, KeyEvent event) {
        if (keyCode == KeyEvent.KEYCODE_BACK
                && event.getAction() == KeyEvent.ACTION_DOWN) {
            return true;
        }
        return super.onKeyDown(keyCode, event);
    }

}
