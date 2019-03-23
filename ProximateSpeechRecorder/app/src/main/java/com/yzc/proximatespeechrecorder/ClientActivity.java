package com.yzc.proximatespeechrecorder;

import android.Manifest;
import android.app.Activity;
import android.content.Context;
import android.content.pm.PackageManager;
import android.graphics.Bitmap;
import android.graphics.BitmapFactory;
import android.graphics.Canvas;
import android.graphics.ImageFormat;
import android.graphics.Paint;
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
import android.media.AudioFormat;
import android.media.AudioRecord;
import android.media.Image;
import android.media.ImageReader;
import android.media.MediaRecorder;
import android.os.Bundle;
import android.os.Environment;
import android.support.v4.app.ActivityCompat;
import android.util.Log;
import android.util.Range;
import android.view.Surface;
import android.view.TextureView;
import android.view.View;
import android.widget.Button;
import android.widget.TextView;

import java.io.BufferedReader;
import java.io.BufferedWriter;
import java.io.File;
import java.io.FileOutputStream;
import java.io.IOException;
import java.io.InputStreamReader;
import java.io.OutputStream;
import java.io.OutputStreamWriter;
import java.net.Socket;
import java.net.UnknownHostException;
import java.nio.ByteBuffer;
import java.util.ArrayList;
import java.util.Arrays;
import java.util.List;

public class ClientActivity extends Activity implements SensorEventListener {

    Socket socketClient, audioSocket;
    private OutputStream audioOutputStream;

    private TextView textView_recv;
    private Button button_connect, button_send;
    private BufferedReader in;
    private BufferedWriter out;
    private String TAG = "ClientActivity";
    private int sensorType[] = {
            Sensor.TYPE_ACCELEROMETER,
            Sensor.TYPE_LINEAR_ACCELERATION,
            Sensor.TYPE_GRAVITY,
            Sensor.TYPE_GYROSCOPE,
            Sensor.TYPE_PROXIMITY
    };

    private String sent = "";

    //Camera2, for same SENSOR_DELAY_GAME
    private String mCameraIdFront;
    private CameraDevice mCameraDevice;
    private MediaRecorder mMediaRecorder;
    private CaptureRequest.Builder mCaptureBuilder;
    private ImageReader mImageReader;
    private CaptureRequest mCaptureRequest;
    private CameraCaptureSession mCaptureSession;
    private Range<Integer>[] fpsRanges;

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        setContentView(R.layout.activity_client);
        initView();
        loadSensor();
        setupCamera();
        openCamera(mCameraIdFront);
    }

    private void loadSensor() {
        SensorManager mSensorManager = (SensorManager) getSystemService(SENSOR_SERVICE);
        if (mSensorManager == null) {
            Log.w(TAG, "no SENSOR_SERVICE");
            return;
        }

        for (int i = 0; i < sensorType.length; i++) {
            Sensor sensor = mSensorManager.getDefaultSensor(sensorType[i]);
            if (sensor != null) {
                Log.i(TAG, "register sensor successful");
                mSensorManager.registerListener(this, sensor, SensorManager.SENSOR_DELAY_GAME);
            } else
                Log.w(TAG, "register sensor failed");
        }

    }

    private void initView() {
        button_connect = findViewById(R.id.button_connect);
        button_send = findViewById(R.id.button_send);
        button_connect.setOnClickListener(clickListener);
        button_send.setOnClickListener(clickListener);
        textView_recv = findViewById(R.id.textView_recv);
    }

    View.OnClickListener clickListener = new View.OnClickListener() {
        @Override
        public void onClick(View view) {
            switch (view.getId()) {
                case R.id.button_connect:
                    SocketManager.getInstance().connect();
                    break;
                case R.id.button_send:
                    startCapture();
                    break;
            }
        }
    };

    @Override
    public void onSensorChanged(SensorEvent sensorEvent) {
        float[] values = sensorEvent.values;
        int type = sensorEvent.sensor.getType();
        if (!SocketManager.getInstance().isConnected())
            return;
        String msg = "";
        switch (type) {
            case Sensor.TYPE_ACCELEROMETER:
                msg = "ACCELEROMETER";
                break;
            case Sensor.TYPE_LINEAR_ACCELERATION:
                msg = "LINEAR_ACCELERATION";
                break;
            case Sensor.TYPE_GRAVITY:
                msg = "GRAVITY";
                break;
            case Sensor.TYPE_GYROSCOPE:
                msg = "GYROSCOPE";
                break;
            case Sensor.TYPE_PROXIMITY:
                msg = "PROXIMITY";
                break;
        }
        msg += " " + sensorEvent.timestamp / 1000000L;
        for (int i = 0; i < values.length; ++i)
            msg += " " + values[i];
        msg += "#";
        Log.i("ClientTrue", msg);
        SocketManager.getInstance().send_motion(msg);
    }

    @Override
    public void onAccuracyChanged(Sensor sensor, int accuracy) {

    }

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

    private ImageReader.OnImageAvailableListener mOnImageAvailableListener =
            new ImageReader.OnImageAvailableListener() {
        @Override
        public void onImageAvailable(ImageReader reader) {
            Image image = reader.acquireLatestImage();
            ByteBuffer buffer = image.getPlanes()[0].getBuffer();
            byte[] bytes = new byte[buffer.remaining()];
            buffer.get(bytes);
            Log.d("ImageReader", String.valueOf(bytes.length));
            Log.d("ImageReader", String.valueOf(image.getWidth()) + " " + String.valueOf(image.getHeight()));
            // save(bytes, file);
            /*Bitmap bitmap = BitmapFactory.decodeByteArray(bytes, 0, bytes.length);

            Bitmap newBitmap = Bitmap.createBitmap(bitmap.getWidth(), bitmap.getHeight(), bitmap.getConfig());
            Canvas canvas = new Canvas(newBitmap);
            Paint paint = new Paint();
            canvas.drawBitmap(bitmap, 500, 500, paint);*/
            image.close();
        }
    };

    private void startCapture() {

        mImageReader = ImageReader.newInstance(108, 192, ImageFormat.JPEG, 2);
        mImageReader.setOnImageAvailableListener(mOnImageAvailableListener, null);
        try {
            mCaptureBuilder = mCameraDevice.createCaptureRequest(CameraDevice.TEMPLATE_PREVIEW);
            List<Surface> surfaces = new ArrayList<>();

            Surface recorderSurface = mImageReader.getSurface();
            surfaces.add(recorderSurface);
            mCaptureBuilder.addTarget(recorderSurface);
            mCaptureBuilder.set(CaptureRequest.CONTROL_AE_TARGET_FPS_RANGE, fpsRanges[fpsRanges.length - 1]);
            Log.d("FPS", "Used fps: " + String.valueOf(fpsRanges[fpsRanges.length - 1]));
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

    private void openCamera(String CameraId) {
        CameraManager manager = (CameraManager) getSystemService(Context.CAMERA_SERVICE);
        try {
            if (ActivityCompat.checkSelfPermission(
                    this, Manifest.permission.CAMERA) != PackageManager.PERMISSION_GRANTED) {
                return;
            }
            manager.openCamera(CameraId, mStateCallback, null);
            CameraCharacteristics characteristics = manager.getCameraCharacteristics(CameraId);
            fpsRanges = characteristics.get(CameraCharacteristics.CONTROL_AE_AVAILABLE_TARGET_FPS_RANGES);
            Log.d("FPS", "SYNC_MAX_LATENCY_PER_FRAME_CONTROL: " + Arrays.toString(fpsRanges));
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
}
