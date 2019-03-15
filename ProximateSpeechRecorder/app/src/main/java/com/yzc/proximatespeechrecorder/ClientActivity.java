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
import android.hardware.camera2.CameraDevice;
import android.hardware.camera2.CameraManager;
import android.media.MediaRecorder;
import android.os.Bundle;
import android.support.v4.app.ActivityCompat;
import android.util.Log;
import android.view.View;
import android.widget.Button;
import android.widget.TextView;

import java.io.BufferedReader;
import java.io.BufferedWriter;
import java.io.IOException;
import java.io.InputStreamReader;
import java.io.OutputStreamWriter;
import java.net.Socket;
import java.net.UnknownHostException;

public class ClientActivity extends Activity implements SensorEventListener {

    private final int port = 8888;
    private final String host = "192.168.1.57";
    Socket socketClient;

    private TextView textView_recv;
    private String msg;
    private Button button_connect, button_send;
    private BufferedReader in;
    private BufferedWriter out;
    private String TAG = "ClientActivity";
    private int sensorType[] = {
            Sensor.TYPE_LINEAR_ACCELERATION,
            Sensor.TYPE_GYROSCOPE,
            Sensor.TYPE_PROXIMITY
    };

    //Camera2
    private String mCameraIdFront;
    private CameraDevice mCameraDevice;
    private MediaRecorder mMediaRecorder;

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        setContentView(R.layout.activity_client);
        initView();
        loadSensor();
        //For same SENSOR_DELAY_GAME
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
            Thread thread;
            switch (view.getId()) {
                case R.id.button_connect:
                    thread=new Thread(){
                        @Override
                        public void run() { tcpClient();}
                    };
                    thread.start();
                    textView_recv.setText(msg);
                    break;
                case R.id.button_send:
                    thread = new Thread() {
                        @Override
                        public void run() {sendClient("1234");}
                    };
                    thread.start();
                    break;
            }
        }
    };

    private void sendClient(String msg) {
        try {
            Log.i(TAG, msg);
            out.write(msg);
            out.flush();
            // Log.i("TcpClient", "receiving");
            // String inMsg = in.readLine() + System.getProperty("line.separator");//服务器返回的数据
            // Log.i("TcpClient", "received: " + inMsg);
        } catch (IOException e) {
            e.printStackTrace();
        }
    }

    private void tcpClient(){
        try {
            Log.i("Client","新建套接字");
            socketClient = new Socket(host, port);
            Log.i("Client","新建套接字有效");
            in = new BufferedReader(new InputStreamReader(socketClient.getInputStream()));
            out = new BufferedWriter(new OutputStreamWriter(socketClient.getOutputStream()));
            // String outMsg = "TCP connecting to " + port + System.getProperty("line.separator");//发出的数据
            // out.write(outMsg);//发送数据
            Log.i("Client","发送数据有效");
            // out.flush();
            // Log.i("TcpClient", "sent: " + outMsg);
            // String inMsg = in.readLine() + System.getProperty("line.separator");//服务器返回的数据
            // Log.i("TcpClient", "received: " + inMsg);
            // msg = inMsg;
            // socketClient.close();
        } catch (UnknownHostException e){e.printStackTrace();}
        catch (IOException e){e.printStackTrace();}
    }

    @Override
    public void onSensorChanged(SensorEvent sensorEvent) {
        float[] values = sensorEvent.values;
        int type = sensorEvent.sensor.getType();
        if (type == Sensor.TYPE_LINEAR_ACCELERATION)
            Log.d(TAG, String.valueOf(sensorEvent.timestamp / 1000000L));
        if (out == null)
            return;
        switch (type) {
            case Sensor.TYPE_LINEAR_ACCELERATION:
                msg = "LINEAR_ACCELERATION";
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
        Thread thread = new Thread() {
            @Override
            public void run() {sendClient(msg);}
        };
        thread.start();
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
}
