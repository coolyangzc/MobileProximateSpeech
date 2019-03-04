package com.yzc.proximatespeechrecorder;

import android.app.Activity;
import android.app.AlertDialog;
import android.content.Context;
import android.content.DialogInterface;
import android.content.Intent;
import android.graphics.Color;
import android.hardware.SensorEventListener;
import android.media.CamcorderProfile;
import android.media.MediaRecorder;
import android.media.MediaScannerConnection;
import android.os.Bundle;
import android.os.Environment;
import android.os.SystemClock;
import android.os.VibrationEffect;
import android.os.Vibrator;
import android.provider.MediaStore;
import android.text.InputType;
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
    private Button button_record, button_goto, button_redo;
    private TextView textView_description, textView_sentence;
    private boolean isRecording = false;
    private File file, audioFile;
    private MediaRecorder mMediaRecorder;
    private Vibrator mVibrator;
    private VoiceTask tasks;

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
        Intent intent = getIntent();
        int seed = intent.getIntExtra("randomSeed", 0);
        tasks = new VoiceTask(seed);
        initViews();
        mMediaRecorder = new MediaRecorder();
        mVibrator = (Vibrator)getApplication().getSystemService(VIBRATOR_SERVICE);
    }

    private void initViews() {
        textView_description = findViewById(R.id.textView_description);
        textView_sentence = findViewById(R.id.textView_sentence);
        textView_description.setText(tasks.getTaskDescription());
        textView_sentence.setText(tasks.getSpeechSentence());
        button_record = findViewById(R.id.button_record);
        button_record.setOnClickListener(clickListener);
        button_goto = findViewById(R.id.button_goto);
        button_goto.setOnLongClickListener(longClickListener);
        button_redo = findViewById(R.id.button_redo);
        button_redo.setOnLongClickListener(longClickListener);
    }

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

    private void vibration() {
        long[] timings = {1000, 100};
        int[] amplitudes = {0, VibrationEffect.DEFAULT_AMPLITUDE};
        if (tasks.getTaskDescription().contains("反面")) {
            timings[0] = 2000;
        }
        if (tasks.getTaskDescription().contains("裤兜")) {
            timings[0] = 5000;
            timings[1] = 1000;
            amplitudes[1] = 255;
        }
        VibrationEffect ve = VibrationEffect.createWaveform(timings, amplitudes, -1);
        mVibrator.vibrate(ve);
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
                        setupMediaRecorder();
                        mMediaRecorder.start();
                        vibration();
                    } else {
                        try {
                            fos.close();
                        } catch (IOException e) {
                            e.printStackTrace();
                        }
                        mMediaRecorder.stop();
                        mMediaRecorder.reset();
                        mMediaRecorder = new MediaRecorder();
                        MediaScannerConnection.scanFile(ctx,
                                new String[] { file.getAbsolutePath(), audioFile.getAbsolutePath() },
                                null, null);
                        textView_description.setText(tasks.nextTask());
                        textView_sentence.setText(tasks.getSpeechSentence());
                    }
                    break;
            }
        }
    };

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
                            textView_sentence.setText(tasks.getSpeechSentence());
                        }
                    });
                    builder.setNegativeButton("否", null);
                    builder.show();
                    break;
                case R.id.button_redo:
                    textView_description.setText(tasks.prevTask());
                    textView_sentence.setText(tasks.getSpeechSentence());
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
        String ss = tasks.getTaskDescription();
        ss += tasks.getSpeechSentence();
        try {
            fos.write(ss.getBytes());
        } catch (IOException e) {
            e.printStackTrace();
        }
    }

    private void setupMediaRecorder() {
        try {
            mMediaRecorder.reset();
            mMediaRecorder.setAudioSource(MediaRecorder.AudioSource.MIC);
            mMediaRecorder.setAudioChannels(2);
            mMediaRecorder.setAudioSamplingRate(44100);
            mMediaRecorder.setAudioEncodingBitRate(16 * 44100);
            mMediaRecorder.setOutputFormat(MediaRecorder.OutputFormat.MPEG_4);
            mMediaRecorder.setAudioEncoder(MediaRecorder.AudioEncoder.AAC);
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
