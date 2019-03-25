package com.yzc.proximatespeechrecorder;

import android.Manifest;
import android.app.Activity;
import android.content.Context;
import android.content.Intent;
import android.content.pm.PackageManager;
import android.os.Environment;
import android.support.v4.app.ActivityCompat;
import android.support.v7.app.AppCompatActivity;
import android.os.Bundle;
import android.view.View;
import android.widget.Button;
import android.widget.EditText;

import java.io.FileInputStream;
import java.io.FileOutputStream;
import java.io.IOException;

public class MainActivity extends AppCompatActivity {

    private Context ctx;
    private EditText et_randomSeed, et_IP;

    private static final int REQUEST_EXTERNAL_STORAGE = 1;
    private static String[] PERMISSIONS_STORAGE = {
            Manifest.permission.READ_EXTERNAL_STORAGE,
            Manifest.permission.WRITE_EXTERNAL_STORAGE,
    };
    private static String[] PERMISSIONS_VIDEO = {
            Manifest.permission.CAMERA,
            Manifest.permission.RECORD_AUDIO
    };

    private final String ipFile =
            Environment.getExternalStorageDirectory().getPath() +
                    "/IP.txt";

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        setContentView(R.layout.activity_main);
        ctx = this;
        initViews();
        verifyStoragePermissions(this);
        verifyVideoPermissions(this);
    }

    private void initViews() {
        Button button_demo = findViewById(R.id.button_demo);
        Button button_record = findViewById(R.id.button_record);
        Button button_study1 = findViewById(R.id.button_study1);
        Button button_voice = findViewById(R.id.button_voice);
        Button button_client = findViewById(R.id.button_client);
        Button button_evaluation = findViewById(R.id.button_evaluation);
        button_demo.setOnClickListener(clickListener);
        button_record.setOnClickListener(clickListener);
        button_study1.setOnClickListener(clickListener);
        button_voice.setOnClickListener(clickListener);
        button_client.setOnClickListener(clickListener);
        button_evaluation.setOnClickListener(clickListener);

        et_randomSeed = findViewById(R.id.editText_randomSeed);
        et_IP = findViewById(R.id.editText_IP);

        try {
            StringBuilder sb = new StringBuilder("");
            FileInputStream inputStream = new FileInputStream(ipFile);
            byte[] buffer = new byte[1024];
            int len = inputStream.read(buffer);
            while (len > 0) {
                sb.append(new String(buffer, 0, len));
                len = inputStream.read(buffer);
            }
            inputStream.close();
            et_IP.setText(sb.toString());
        } catch (IOException e) {
            e.printStackTrace();
        }

    }

    View.OnClickListener clickListener = new View.OnClickListener() {
        @Override
        public void onClick(View view) {
            Intent intent = new Intent();
            String seed = et_randomSeed.getText().toString();
            if (seed.equals(""))
                intent.putExtra("randomSeed", 0);
            else
                intent.putExtra("randomSeed", Integer.valueOf(seed));
            String host_ip = et_IP.getText().toString();
            intent.putExtra("HOST_IP", host_ip);

            switch (view.getId()) {
                case R.id.button_demo:
                    intent.setClass(ctx, DemoActivity.class);
                    startActivity(intent);
                    break;
                case R.id.button_record:
                    intent.setClass(ctx, SensorActivity.class);
                    startActivity(intent);
                    break;
                case R.id.button_study1:
                    intent.setClass(ctx, Study1Activity.class);
                    startActivity(intent);
                    break;
                case R.id.button_voice:
                    intent.setClass(ctx, VoiceActivity.class);
                    startActivity(intent);
                    break;
                case R.id.button_client:
                    intent.setClass(ctx, ClientActivity.class);
                    startActivity(intent);
                    break;
                case R.id.button_evaluation:
                    try {
                        FileOutputStream out = new FileOutputStream(ipFile);
                        out.write(host_ip.getBytes());
                        out.flush();
                        out.close();
                    } catch (IOException e) {
                        e.printStackTrace();
                    }
                    intent.setClass(ctx, EvaluationActivity.class);
                    startActivity(intent);
                    break;
            }
        }
    };

    public static void verifyStoragePermissions(Activity activity) {
        int permission = ActivityCompat.checkSelfPermission(activity,
                Manifest.permission.WRITE_EXTERNAL_STORAGE);
        if (permission != PackageManager.PERMISSION_GRANTED) {
            // We don't have permission so prompt the user
            ActivityCompat.requestPermissions(
                    activity,
                    PERMISSIONS_STORAGE,
                    REQUEST_EXTERNAL_STORAGE);
        }
    }

    public static void verifyVideoPermissions(Activity activity) {
        int permission = ActivityCompat.checkSelfPermission(activity,
                Manifest.permission.CAMERA);
        if (permission != PackageManager.PERMISSION_GRANTED) {
            ActivityCompat.requestPermissions(
                    activity,
                    PERMISSIONS_VIDEO,
                    REQUEST_EXTERNAL_STORAGE);
        }
    }
}