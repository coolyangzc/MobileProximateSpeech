package com.yzc.proximatespeechrecorder;

import android.app.Activity;
import android.hardware.Sensor;
import android.hardware.SensorEvent;
import android.hardware.SensorEventListener;
import android.hardware.SensorManager;
import android.os.Bundle;
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

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        setContentView(R.layout.activity_client);
        initView();
        loadSensor();
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
            String outMsg = "TCP connecting to " + port + System.getProperty("line.separator");//发出的数据
            out.write(outMsg);//发送数据
            Log.i("Client","发送数据有效");
            out.flush();
            Log.i("TcpClient", "sent: " + outMsg);
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
        msg += '\n';

        Thread thread = new Thread() {
            @Override
            public void run() {sendClient(msg);}
        };
        thread.start();
    }

    @Override
    public void onAccuracyChanged(Sensor sensor, int accuracy) {

    }
}
