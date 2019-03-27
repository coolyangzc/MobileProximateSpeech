package com.yzc.proximatespeechrecorder;

import android.Manifest;
import android.app.Activity;
import android.app.AlertDialog;
import android.content.Context;
import android.content.DialogInterface;
import android.content.Intent;
import android.content.pm.PackageManager;
import android.graphics.Bitmap;
import android.graphics.BitmapFactory;
import android.graphics.Color;
import android.graphics.ImageFormat;
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
import android.media.Image;
import android.media.ImageReader;
import android.media.MediaRecorder;
import android.media.MediaScannerConnection;
import android.os.Bundle;
import android.os.Environment;
import android.os.SystemClock;
import android.os.VibrationEffect;
import android.os.Vibrator;
import android.support.annotation.NonNull;
import android.support.v4.app.ActivityCompat;
import android.text.InputType;
import android.util.Log;
import android.util.Range;
import android.view.KeyEvent;
import android.view.Surface;
import android.view.View;
import android.widget.Button;
import android.widget.EditText;
import android.widget.TextView;

import java.io.ByteArrayOutputStream;
import java.io.File;
import java.io.FileOutputStream;
import java.io.IOException;
import java.nio.ByteBuffer;
import java.text.SimpleDateFormat;
import java.util.ArrayList;
import java.util.Arrays;
import java.util.Date;
import java.util.List;
import java.util.Locale;
import java.util.Random;

public class EvaluationActivity extends Activity implements SensorEventListener {

    private String TAG = "EvaluationActivity";
    private int sensorType[] = {
            Sensor.TYPE_ACCELEROMETER,
            Sensor.TYPE_LINEAR_ACCELERATION,
            Sensor.TYPE_GRAVITY,
            Sensor.TYPE_GYROSCOPE,
            Sensor.TYPE_PROXIMITY,
            Sensor.TYPE_MAGNETIC_FIELD
    };
    private float sensorData[][] = new float[sensorType.length][];

    private Context ctx;

    private FileOutputStream fos;
    private File file, audioFile;
    private final String pathName =
            Environment.getExternalStorageDirectory().getPath() +
                    "/SensorData/Evaluation/";
    private final String picPath =
            Environment.getExternalStorageDirectory().getPath() +
                    "/SensorData/Evaluation/pic/";
    private String curPathName;
    private Vibrator mVibrator;

    //Camera2, for same SENSOR_DELAY_GAME
    private String mCameraIdFront;
    private CameraDevice mCameraDevice;
    private MediaRecorder mMediaRecorder;
    private CaptureRequest.Builder mCaptureBuilder;
    private ImageReader mImageReader;
    private CaptureRequest mCaptureRequest;
    private CameraCaptureSession mCaptureSession;

    private TextView textView_task, textView_sentence;
    private Button button_connect, button_record, button_redo, button_goto;
    private String sentences[] = VoiceTask.singleCommands;

    private String fileName;
    private Long startTimestamp, startUpTimeMillis, startTimeMillis;
    private Long rapidTimestamp = 0L, motionTimestamp = 0L;

    //experiment state
    private boolean isRecording = false, has_triggerd = false;
    private int task_id = 0, remaining_img = -1, img_cnt = 0;
    private Random random = new Random();

    private float last_motion_predict = -1;
    private ArrayList<Float> motion_res = new ArrayList<Float> (Arrays.asList(0f, 0f, 0f, 0f, 0f));
    private ArrayList<Float> img_res = new ArrayList<Float> ();
    private boolean proximityHasZero = false, orientationOK = false;


    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        setContentView(R.layout.activity_evaluation);

        initView();
        loadSensor();
        setupCamera();
        openCamera(mCameraIdFront);

        Intent intent = getIntent();
        String Host_IP = intent.getStringExtra("HOST_IP");
        SocketManager.getInstance().setHOSTIP(Host_IP);
        mMediaRecorder = new MediaRecorder();
        mVibrator = (Vibrator)getApplication().getSystemService(VIBRATOR_SERVICE);
        setTask(task_id);
    }

    private void initView() {
        ctx = this;

        button_connect = findViewById(R.id.button_connect);
        button_connect.setOnClickListener(clickListener);
        button_connect.setTextColor(Color.RED);

        button_record = findViewById(R.id.button_record);
        button_record.setOnClickListener(clickListener);

        button_redo = findViewById(R.id.button_redo);
        button_redo.setOnLongClickListener(longClickListener);

        button_goto = findViewById(R.id.button_goto);
        button_goto.setOnLongClickListener(longClickListener);

        textView_task = findViewById(R.id.textView_task);
        textView_sentence = findViewById(R.id.textView_sentence);
        textView_sentence.setTextColor(Color.BLACK);
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

    View.OnClickListener clickListener = new View.OnClickListener() {
        @Override
        public void onClick(View view) {
            switch (view.getId()) {
                case R.id.button_connect:
                    if (!SocketManager.getInstance().isConnected()) {
                        SocketManager.getInstance().connect();
                        SocketManager.getInstance().motion_res = motion_res;
                        SocketManager.getInstance().img_res = img_res;
                        startCapture();
                    }
                    button_connect.setText("");
                    break;
                case R.id.button_record:
                    isRecording ^= true;
                    changeButtonText(isRecording);
                    if (isRecording) {
                        createDataFile();
                        if (task_id <= 10) {
                            setupMediaRecorder();
                            SocketManager.getInstance().send_motion("START " + fileName + "#");
                            mMediaRecorder.start();
                        }
                    } else {
                        closeTxtFile();
                        if (task_id <= 10) {
                            mMediaRecorder.stop();
                            mMediaRecorder.reset();
                            SocketManager.getInstance().send_motion("END " + fileName + "#");
                            mMediaRecorder = new MediaRecorder();
                        }
                        MediaScannerConnection.scanFile(ctx,
                                new String[]{file.getAbsolutePath(), audioFile.getAbsolutePath()},
                                null, null);
                        task_id += 1;
                        if (task_id > 20)
                            task_id = 0;
                        setTask(task_id);
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
                case R.id.button_redo:
                    if (task_id > 0)
                        task_id -= 1;
                    setTask(task_id);
                    break;
                case R.id.button_goto:
                    AlertDialog.Builder builder = new AlertDialog.Builder(ctx);
                    builder.setTitle("跳转至");
                    final EditText et = new EditText(ctx);
                    et.setInputType(InputType.TYPE_CLASS_NUMBER);
                    builder.setView(et);
                    builder.setPositiveButton("是", new DialogInterface.OnClickListener() {
                        @Override
                        public void onClick(DialogInterface dialog, int which) {
                            task_id = Integer.valueOf(et.getText().toString());
                            if (task_id < 0)
                                task_id = 0;
                            else if (task_id > 20)
                                task_id = 20;
                            setTask(task_id);
                        }
                    });
                    builder.setNegativeButton("否", null);
                    builder.show();
                    break;
            }
            return false;
        }
    };

    private void setTask(int task_id) {
        has_triggerd = false;
        proximityHasZero = (sensorData[4] == null || sensorData[4][2] == 0);
        img_res.clear();
        remaining_img = -1; img_cnt = 0;

        String task = String.valueOf(task_id) + " / 20\n";
        if (task_id <= 10) {
            int n = sentences.length;
            textView_sentence.setText(sentences[random.nextInt(n)]);
            if (task_id == 0)
                task += "近距离说话（测试）";
            else if (task_id <= 5)
                task += "近距离说话（右手）";
            else
                task += "近距离说话（左手）";
        } else {
            textView_sentence.setText("");
            if (task_id <= 15)
                task += "接听电话（右手）";
            else
                task += "接听电话（左手）";
        }
        if (task_id == 1 || task_id == 6 || task_id == 11 || task_id == 16)
            textView_task.setTextColor(Color.RED);
        else
            textView_task.setTextColor(Color.BLACK);
        textView_task.setText(task);

    }

    private void createDataFile() {
        try {
            SimpleDateFormat format = new SimpleDateFormat("yyMMdd HH_mm_ss", Locale.US);
            fileName = format.format(new Date()) + " " + String.valueOf(task_id);
            curPathName = pathName +
                    new SimpleDateFormat("yyMMdd", Locale.US).format(new Date()) + "/";
            File path = new File(curPathName);
            file = new File(curPathName + fileName + ".txt");
            boolean res;
            if (!path.exists())
                res = path.mkdir();
            if (!file.exists())
                res = file.createNewFile();
            fos = new FileOutputStream(file);
            if (task_id <= 10)
                audioFile = new File(curPathName + fileName + ".mp4");
        } catch (IOException e) {
            e.printStackTrace();
        }
        String ss = textView_task.getText().toString() + '\n';
        ss += textView_sentence.getText().toString() + '\n';
        startTimeMillis = System.currentTimeMillis();
        startUpTimeMillis = SystemClock.uptimeMillis();
        startTimestamp = SystemClock.elapsedRealtimeNanos();
        ss += Long.toString(startTimeMillis) + "\n";
        ss += Long.toString(startUpTimeMillis) + "\n";
        ss += Long.toString(startTimestamp) + "\n";
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

    private void loadSensor() {
        SensorManager mSensorManager = (SensorManager) getSystemService(SENSOR_SERVICE);
        if (mSensorManager == null) {
            Log.w(TAG, "no SENSOR_SERVICE");
            return;
        }

        for(int sensorID:sensorType) {
            Sensor sensor = mSensorManager.getDefaultSensor(sensorID);
            if (sensor != null) {
                mSensorManager.registerListener(this, sensor, SensorManager.SENSOR_DELAY_GAME);
                Log.i(TAG, "register sensor successful");
            } else
                Log.w(TAG, "register sensor failed");
        }
    }

    private void closeTxtFile() {
        try {
            if (task_id > 10 && !has_triggerd) {
                String s = "NOTRIGGER";
                for (float img_predict : img_res)
                    s += " " + String.valueOf(img_predict);
                s += "\n";
                fos.write(s.getBytes());
            }
            fos.close();
        } catch (IOException e) {
            e.printStackTrace();
        }
    }


    @Override
    public void onSensorChanged(SensorEvent event) {
        float[] values = event.values;
        int type = event.sensor.getType();
        for (int i = 0; i < sensorType.length; i++) {
            if (event.sensor.getType() == sensorType[i]) {
                sensorData[i] = values;
                break;
            }
        }
        if (!SocketManager.getInstance().isConnected())
            return;
        String name = "", s = "";
        switch (type) {
            case Sensor.TYPE_ACCELEROMETER:
                name = "ACCELEROMETER";
                if (last_motion_predict != motion_res.get(4)) {
                    last_motion_predict = motion_res.get(4);
                    if (isRecording && startTimestamp != null)
                        s = "MOTION_PREDICT " +
                                Long.toString((event.timestamp - startTimestamp) / 1000000L)
                                + " " + String.valueOf(last_motion_predict) + "\n";
                }
                break;
            case Sensor.TYPE_LINEAR_ACCELERATION:
                name = "LINEAR_ACCELERATION";
                if (values[2] > 0 || values[0] + values[1] + values[2] > 0)
                    rapidTimestamp = event.timestamp;
                else if (task_id <= 10 && event.timestamp - rapidTimestamp >= 2000 * 1000000L)
                    break;
                if (!isRecording || has_triggerd)
                    break;
                if (sensorData[4][2] > 0 && proximityHasZero && orientationOK) {
                    if (motion_res.get(4) > 0.5)
                        motionTimestamp = event.timestamp;
                    if (motion_res.get(4) > 0.5 ||
                            (task_id > 10 && event.timestamp - motionTimestamp <= 1000 * 1000000L)) {
                        if (task_id > 10) {
                            if (img_res.size() < 5)
                                break;
                            String tmp = "";
                            for (float r:img_res)
                                tmp += " " + String.valueOf(r);
                            Log.d("IMG_RES", tmp);
                            float sum = 0;
                            for (float img_predict:img_res)
                                sum += img_predict;
                            if (sum <= 2.5)
                                break;
                        }
                        VibrationEffect ve = VibrationEffect.createOneShot(100, 1);
                        mVibrator.vibrate(ve);
                        s = "TRIGGER " +
                                Long.toString((event.timestamp - startTimestamp) / 1000000L);
                        if (task_id <= 10)
                            s += " " + String.valueOf(motion_res.get(4)) + "\n";
                        else {
                            for (float img_predict : img_res)
                                s += " " + String.valueOf(img_predict);
                            s += "\n";
                        }
                        has_triggerd = true;
                    }
                }

                break;
            case Sensor.TYPE_GRAVITY:
                name = "GRAVITY";
                float[] ori = new float[3];
                float[] R = new float[9];
                float[] gravity = values;
                float[] geomagnetic = sensorData[5];
                if (gravity != null && geomagnetic != null &&
                        SensorManager.getRotationMatrix(R, null, gravity, geomagnetic)) {
                    SensorManager.getOrientation(R, ori);
                    orientationOK = Math.toDegrees(ori[1]) < -50;
                }
                break;
            case Sensor.TYPE_GYROSCOPE:
                name = "GYROSCOPE";
                break;
            case Sensor.TYPE_PROXIMITY:
                name = "PROXIMITY";
                if (values[2] == 0)
                    proximityHasZero = true;
                else if (remaining_img <= -1 && isRecording) {
                    remaining_img = 7;
                    img_cnt = 0;
                }
                break;
            case Sensor.TYPE_MAGNETIC_FIELD:
                return;
                //break;
        }
        String msg = name + " " + event.timestamp / 1000000L;
        for (int i = 0; i < values.length; ++i)
            msg += " " + values[i];
        msg += "#";
        SocketManager.getInstance().send_motion(msg);

        if (!isRecording)
            return;
        s += name + " " + Long.toString((event.timestamp - startTimestamp) / 1000000L);
        s += " " + Integer.toString(event.accuracy);
        for (float data : event.values)
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

    /**
     * *************************************Camera2*************************************************
     */
    private void setupCamera() {
        try {
            CameraManager manager = (CameraManager) getSystemService(Context.CAMERA_SERVICE);
            if (manager != null)
                mCameraIdFront = manager.getCameraIdList()[1];
            else
                Log.w(TAG, "getSystemService failed");
            mMediaRecorder = new MediaRecorder();
            CameraCharacteristics characteristics = manager.getCameraCharacteristics(mCameraIdFront);
            Range<Integer>[] fpsRanges = characteristics.get(CameraCharacteristics.CONTROL_AE_AVAILABLE_TARGET_FPS_RANGES);
            Log.d("FPS", "SYNC_MAX_LATENCY_PER_FRAME_CONTROL: " + Arrays.toString(fpsRanges));
        } catch (Exception e) {
            e.printStackTrace();
        }
    }

    private void savePic(Bitmap bitmap, int id) {
        try {
            File picFile = new File(picPath +
                    fileName + " " + String.valueOf(id) + ".jpg");
            FileOutputStream out = new FileOutputStream(picFile);
            if(bitmap.compress(Bitmap.CompressFormat.JPEG, 100, out))
            {
                out.flush();
                out.close();
            }
            MediaScannerConnection.scanFile(ctx,
                    new String[]{picFile.getAbsolutePath()},
                    null, null);
            Log.d("savePic", picFile.getAbsolutePath());
        } catch (IOException e) {
            e.printStackTrace();
        }
    }

    private ImageReader.OnImageAvailableListener mOnImageAvailableListener =
            new ImageReader.OnImageAvailableListener() {
                @Override
                public void onImageAvailable(ImageReader reader) {
                    Image image = reader.acquireLatestImage();
                    if (image == null)
                        return;
                    ByteBuffer buffer = image.getPlanes()[0].getBuffer();
                    byte[] bytes = new byte[buffer.remaining()];
                    buffer.get(bytes);
                    image.close();
                    if (!SocketManager.getInstance().isConnected())
                        return;
                    img_cnt += 1;
                    if (img_cnt >= 3)
                        img_cnt = 0;
                    if (remaining_img > 0 && img_cnt == 0) {
                        if (remaining_img >= 6) {
                            remaining_img -= 1;
                            return;
                        }
                        final Bitmap oriBitmap = BitmapFactory.decodeByteArray(bytes, 0, bytes.length);
                        final int id = 5 - remaining_img;
                        new Thread(new Runnable() {
                            @Override
                            public void run() {
                                savePic(oriBitmap, id);
                            }
                        }).start();
                        remaining_img -= 1;
                        if (task_id > 10) {
                            Bitmap newBitmap = Bitmap.createScaledBitmap(oriBitmap, 192, 108, false);
                            ByteArrayOutputStream outStream = new ByteArrayOutputStream();
                            newBitmap.compress(Bitmap.CompressFormat.JPEG, 100, outStream);
                            bytes = outStream.toByteArray();
                            Log.d("ImageReader", String.valueOf(bytes.length));
                            SocketManager.getInstance().send_img(bytes);
                        }
                    }
                }
            };

    private void startCapture() {

        mImageReader = ImageReader.newInstance(1920, 1080, ImageFormat.JPEG, 2);
        mImageReader.setOnImageAvailableListener(mOnImageAvailableListener, null);
        try {
            mCaptureBuilder = mCameraDevice.createCaptureRequest(CameraDevice.TEMPLATE_PREVIEW);
            List<Surface> surfaces = new ArrayList<>();

            Surface recorderSurface = mImageReader.getSurface();
            surfaces.add(recorderSurface);
            mCaptureBuilder.addTarget(recorderSurface);
            // mCaptureBuilder.set(CaptureRequest.CONTROL_AE_TARGET_FPS_RANGE, fpsRanges[fpsRanges.length - 1]);
            Range<Integer> fpsRange = new Range<>(15, 15);
            mCaptureBuilder.set(CaptureRequest.CONTROL_AE_TARGET_FPS_RANGE, fpsRange);
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
            assert manager != null;
            manager.openCamera(CameraId, mStateCallback, null);
        } catch (CameraAccessException e) {
            e.printStackTrace();
        }


    }

    private CameraDevice.StateCallback mStateCallback = new CameraDevice.StateCallback() {
        @Override
        public void onOpened(@NonNull CameraDevice camera) {
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

    @Override
    public boolean onKeyDown(int keyCode, KeyEvent event) {
        if (keyCode == KeyEvent.KEYCODE_BACK
                && event.getAction() == KeyEvent.ACTION_DOWN) {
            return true;
        }
        return super.onKeyDown(keyCode, event);
    }
}
