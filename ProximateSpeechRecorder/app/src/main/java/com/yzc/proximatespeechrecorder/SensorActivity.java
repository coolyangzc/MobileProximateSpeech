package com.yzc.proximatespeechrecorder;

import android.Manifest;
import android.app.Activity;
import android.content.Context;
import android.content.pm.PackageManager;
import android.hardware.Sensor;
import android.hardware.SensorEvent;
import android.hardware.SensorEventListener;
import android.hardware.SensorManager;
import android.hardware.camera2.CameraAccessException;
import android.hardware.camera2.CameraCaptureSession;
import android.hardware.camera2.CameraCharacteristics;
import android.hardware.camera2.CameraDevice;
import android.hardware.camera2.CameraManager;
import android.hardware.camera2.CaptureRequest;
import android.hardware.camera2.CaptureResult;
import android.hardware.camera2.TotalCaptureResult;
import android.media.CamcorderProfile;
import android.media.MediaRecorder;
import android.media.MediaScannerConnection;
import android.os.Bundle;
import android.os.Environment;
import android.os.SystemClock;
import android.support.v4.app.ActivityCompat;
import android.util.Log;
import android.view.MotionEvent;
import android.view.Surface;
import android.view.View;
import android.widget.ArrayAdapter;
import android.widget.Button;
import android.widget.Spinner;
import android.widget.TextView;
import android.widget.Toast;

import java.io.File;
import java.io.FileOutputStream;
import java.io.IOException;
import java.text.SimpleDateFormat;
import java.util.ArrayList;
import java.util.Arrays;
import java.util.Date;
import java.util.List;
import java.util.Locale;


public class SensorActivity extends Activity implements SensorEventListener {

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
    private float focusDistance = 0;

    private SensorManager mSensorManager;
    private TextView textView_sensor, textView_touch;
    private Spinner spinner_from, spinner_to;
    private Button button_record;

    private int sensorType[] = SensorUtil.sensorType;
    private String sensorName[] = SensorUtil.sensorName;

    private float sensorData[][] = new float[sensorType.length][];

    private Study1Task task = new Study1Task(0);

    private final String pathName =
            Environment.getExternalStorageDirectory().getPath() +
                    "/SensorData/Study2/";
    private FileOutputStream fos;

    static {
        System.loadLibrary("native-lib");
    }

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        setContentView(R.layout.activity_sensor);
        ctx = this;
        initViews();
        loadSensor();
        setupCamera();
        openCamera(mCameraIdFront);
    }

    private void initViews() {
        textView_sensor = findViewById(R.id.textView_recv);
        textView_touch = findViewById(R.id.textView_touch);
        button_record = findViewById(R.id.button_record);
        button_record.setOnClickListener(clickListener);

        spinner_from = findViewById(R.id.spinner_from);
        spinner_to = findViewById(R.id.spinner_to);
        setSpinners();
    }

    private void setSpinners() {
        List<String> to_list = new ArrayList<String>();

        List<String> from_list = new ArrayList<String>(Arrays.asList(task.triggerPosition));

        to_list.add("Study2");

        ArrayAdapter<String> arr_adapter= new ArrayAdapter<String>
                (this, android.R.layout.simple_spinner_item, from_list);
        arr_adapter.setDropDownViewResource(android.R.layout.simple_spinner_dropdown_item);
        spinner_from.setAdapter(arr_adapter);

        arr_adapter = new ArrayAdapter<String>
                (this, android.R.layout.simple_spinner_item, to_list);
        arr_adapter.setDropDownViewResource(android.R.layout.simple_spinner_dropdown_item);
        spinner_to.setAdapter(arr_adapter);
    }

    View.OnClickListener clickListener = new View.OnClickListener() {
        @Override
        public void onClick(View view) {

            switch (view.getId()) {
                case R.id.button_record:
                    isRecording ^= true;
                    if (isRecording) {
                        button_record.setText("Stop Recording");
                        createDataFile();
                        prepareMediaRecorder();
                        startMediaRecorder();
                        readDiffStart();
                    } else {
                        button_record.setText("Start Recording");
                        try {
                            fos.close();
                        } catch (IOException e) {
                            e.printStackTrace();
                        }
                        stopMediaRecorder();
                        readDiffStop();
                        MediaScannerConnection.scanFile(ctx,
                                new String[] { file.getAbsolutePath(), videoFile.getAbsolutePath() }, null, null);

                    }
                    break;
            }
        }
    };

    @Override
    protected void onResume() {
        super.onResume();
        //mSensorManager.registerListener(this, mAccelerometer, SensorManager.SENSOR_DELAY_NORMAL);
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

        //Calc Orientation
        float[] ori = new float[3];
        float[] R = new float[9];
        float[] gravity = sensorData[SensorUtil.getSensorID("GRAVITY")];
        float[] geomagnetic = sensorData[SensorUtil.getSensorID("MAGNETIC_FIELD")];
        if (gravity != null && geomagnetic != null &&
                SensorManager.getRotationMatrix(R, null, gravity, geomagnetic)) {
            SensorManager.getOrientation(R, ori);
            sb.append("Orientation");
            for (float data : ori)
                sb.append(String.format(Locale.US, " %.2f", Math.toDegrees(data)));
            sb.append("\n");
        }
        sb.append("Focus");
        sb.append(String.format(Locale.US, " %.2f", focusDistance));
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

        for (int i = 0; i < e.getPointerCount(); ++i) {
            int id = e.getPointerId(i);
            int x = (int) e.getX(i), y = (int) e.getY(i);
            float p = e.getPressure(i);
            float s = e.getSize(i);
            float o = e.getOrientation(i);

            text += "Id:" + id + " X:" + x + " Y:" + y;
            text += String.format(Locale.US," S:%.2f P:%.2f O:%.6f", s, p, o) + "\n";
            text += String.format(Locale.US, "Tool Major: %.2f Minus: %.2f", e.getToolMajor(i), e.getToolMinor(i)) + "\n";
            text += String.format(Locale.US, "Touch Major: %.2f Minus: %.2f", e.getTouchMajor(i), e.getTouchMinor(i)) + "\n";

        }
        if (e.getAction() == MotionEvent.ACTION_UP)
            text = "";
        textView_touch.setText(text);

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
        String ss = spinner_from.getSelectedItem().toString() +
                " " + spinner_to.getSelectedItem().toString() + "\n";
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
            setUpMediaRecorder();

            mCaptureBuilder = mCameraDevice.createCaptureRequest(CameraDevice.TEMPLATE_RECORD);
            List<Surface> surfaces = new ArrayList<>();

            Surface recorderSurface = mMediaRecorder.getSurface();
            surfaces.add(recorderSurface);
            mCaptureBuilder.addTarget(recorderSurface);
            mCaptureBuilder.set(CaptureRequest.CONTROL_AF_MODE,
                    CaptureRequest.CONTROL_AF_MODE_AUTO);

            mCameraDevice.createCaptureSession(surfaces, new CameraCaptureSession.StateCallback() {
                @Override
                public void onConfigured(CameraCaptureSession session) {
                    try {
                        mCaptureRequest = mCaptureBuilder.build();
                        mCaptureSession = session;
                        mCaptureSession.setRepeatingRequest(mCaptureRequest, mCaptureCallback, null);
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


    private CameraCaptureSession.CaptureCallback mCaptureCallback
            = new CameraCaptureSession.CaptureCallback() {
        @Override
        public void onCaptureCompleted(CameraCaptureSession session, CaptureRequest request, TotalCaptureResult result) {
            super.onCaptureCompleted(session, request, result);
            focusDistance = result.get(CaptureResult.LENS_FOCUS_DISTANCE);
        }
    };

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

    private void setUpMediaRecorder() {
        try {
            Log.d(TAG, "setUpMediaRecorder");
            mMediaRecorder.reset();
            mMediaRecorder.setAudioSource(MediaRecorder.AudioSource.MIC);
            mMediaRecorder.setVideoSource(MediaRecorder.VideoSource.SURFACE);
            if (CamcorderProfile.hasProfile(CamcorderProfile.QUALITY_1080P)) {
                CamcorderProfile profile = CamcorderProfile.get(CamcorderProfile.QUALITY_1080P);
                //profile.videoBitRate = mPreviewSize.getWidth() * mPreviewSize.getHeight();
                profile.videoBitRate = 20 * 1920 * 1080;
                mMediaRecorder.setProfile(profile);
            }
            mMediaRecorder.setOutputFile(videoFile);
            mMediaRecorder.setOrientationHint(270);
            mMediaRecorder.prepare();
        } catch (Exception e) {
            e.printStackTrace();
        }
    }
}

