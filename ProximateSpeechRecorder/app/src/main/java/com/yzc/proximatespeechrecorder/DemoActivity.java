package com.yzc.proximatespeechrecorder;

import android.app.Activity;
import android.content.Context;
import android.os.Bundle;

public class DemoActivity extends Activity {

    private Context ctx;

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        setContentView(R.layout.activity_sensor);
        ctx = this;
        loadSensor();
        setupCamera();
        openCamera(mCameraIdFront);
    }
}
