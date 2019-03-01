package com.yzc.proximatespeechrecorder;

import android.app.Activity;
import android.app.AlertDialog;
import android.content.Context;
import android.content.DialogInterface;
import android.graphics.Color;
import android.hardware.SensorEventListener;
import android.media.CamcorderProfile;
import android.media.MediaRecorder;
import android.media.MediaScannerConnection;
import android.os.Bundle;
import android.os.Environment;
import android.os.SystemClock;
import android.provider.MediaStore;
import android.util.Log;
import android.view.KeyEvent;
import android.view.View;
import android.widget.Button;
import android.widget.EditText;
import android.widget.TextView;

import java.io.File;
import java.io.FileOutputStream;
import java.io.IOException;
import java.text.SimpleDateFormat;
import java.util.Date;
import java.util.Locale;

public class VoiceActivity extends Activity {

    private Context ctx;
    private Button button_record, button_goto;
    private TextView textView_description;
    private boolean isRecording = false;
    private File file, audioFile;
    private MediaRecorder mMediaRecorder = new MediaRecorder();
    private Study1Task tasks = new Study1Task();

    private String TAG = "VoiceActivity";

    private final String pathName =
            Environment.getExternalStorageDirectory().getPath() +
                    "/SensorData/Voice/";
    private FileOutputStream fos;

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        setContentView(R.layout.activity_voice);
        ctx = this;
        initViews();
    }

    private void initViews() {
        textView_description = findViewById(R.id.textView_description);
        textView_description.setText(tasks.getTaskDescription());
        button_record = findViewById(R.id.button_record);
        button_record.setOnClickListener(clickListener);
        button_goto = findViewById(R.id.button_goto);
        button_goto.setOnLongClickListener(longClickListener);
    }

    View.OnClickListener clickListener = new View.OnClickListener() {
        @Override
        public void onClick(View view) {
            switch (view.getId()) {
                case R.id.button_record:
                    isRecording ^= true;
                    if (isRecording) {
                        button_record.setText("结束");
                        button_record.setTextColor(Color.RED);
                        createDataFile();
                        setupMediaRecorder();
                        mMediaRecorder.start();

                    } else {
                        button_record.setText("开始");
                        button_record.setTextColor(Color.BLACK);
                        try {
                            fos.close();
                        } catch (IOException e) {
                            e.printStackTrace();
                        }
                        mMediaRecorder.stop();
                        mMediaRecorder.reset();
                        MediaScannerConnection.scanFile(ctx,
                                new String[] { file.getAbsolutePath(), audioFile.getAbsolutePath() },
                                null, null);
                        textView_description.setText(tasks.nextTask());
                    }
                    break;
            }
        }
    };

    View.OnLongClickListener longClickListener = new View.OnLongClickListener() {

        @Override
        public boolean onLongClick(View v) {
            switch (v.getId()) {
                case R.id.button_goto:
                    AlertDialog.Builder builder = new AlertDialog.Builder(ctx);
                    builder.setTitle("跳转至");
                    final EditText et = new EditText(ctx);
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
            }
            return false;
        }
    };

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
            audioFile = new File(curPathName + fileName + ".mp4");
        } catch (IOException e) {
            e.printStackTrace();
        }

    }

    private void setupMediaRecorder() {
        try {
            mMediaRecorder.reset();
            mMediaRecorder.setAudioSource(MediaRecorder.AudioSource.MIC);
            mMediaRecorder.setAudioChannels(2);
            mMediaRecorder.setAudioEncoder(MediaRecorder.AudioEncoder.DEFAULT);
            mMediaRecorder.setOutputFormat(MediaRecorder.OutputFormat.MPEG_4);
            mMediaRecorder.setOutputFile(audioFile);
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
