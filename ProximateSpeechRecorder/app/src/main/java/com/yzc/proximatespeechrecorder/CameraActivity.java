package com.yzc.proximatespeechrecorder;

import android.Manifest;
import android.app.Activity;
import android.content.Context;
import android.content.Intent;
import android.content.pm.PackageManager;
import android.graphics.ImageFormat;
import android.graphics.Matrix;
import android.graphics.RectF;
import android.graphics.SurfaceTexture;
import android.hardware.camera2.CameraAccessException;
import android.hardware.camera2.CameraCaptureSession;
import android.hardware.camera2.CameraCharacteristics;
import android.hardware.camera2.CameraDevice;
import android.hardware.camera2.CameraManager;
import android.hardware.camera2.CaptureRequest;
import android.hardware.camera2.params.StreamConfigurationMap;
import android.media.CamcorderProfile;
import android.media.Image;
import android.media.ImageReader;
import android.media.MediaRecorder;
import android.os.Bundle;
import android.os.Handler;
import android.os.HandlerThread;
import android.os.Message;
import android.support.v4.app.ActivityCompat;
import android.text.TextUtils;
import android.util.Log;
import android.util.Size;
import android.view.Surface;
import android.view.TextureView;
import android.view.View;
import android.view.Window;
import android.view.WindowManager;
import android.widget.Button;
import android.widget.Toast;

import java.io.FileOutputStream;
import java.io.IOException;
import java.nio.ByteBuffer;
import java.text.SimpleDateFormat;
import java.util.ArrayList;
import java.util.Arrays;
import java.util.Collections;
import java.util.Comparator;
import java.util.Date;
import java.util.List;

public class CameraActivity extends Activity implements TextureView.SurfaceTextureListener {

    //constant
    private static final String TAG = "Camera2RecordActivity";
    private static final int CAPTURE_OK = 0;//拍照完成回调
    private String mCameraId;//后置摄像头ID
    private String mCameraIdFront;//前置摄像头ID
    private Size mPreviewSize;//预览的Size
    private Size mCaptureSize;//拍照Size
    private int width;//TextureView的宽
    private int height;//TextureView的高
    private boolean isCameraFront = true;//当前是否是前置摄像头
    private boolean isLightOn = false;//当前闪光灯是否开启

    //Camera2
    private CameraDevice mCameraDevice;
    private CaptureRequest.Builder mPreviewBuilder;
    private CaptureRequest mCaptureRequest;
    private CameraCaptureSession mPreviewSession;
    private CameraCharacteristics characteristics;
    private ImageReader mImageReader;
    private int mSensorOrientation;
    private String picSavePath;//图片保存路径
    private String videoSavePath;//视频保存路径

    //handler
    private HandlerThread mCameraThread;
    private Handler mCameraHandler;
    private TextureView mTextureView;

    //录像
    private static final int MAX_RECORD_TIME = Camera2Config.RECORD_MAX_TIME;//最大录制时长,默认10S
    private static final int MIN_RECORD_TIME = Camera2Config.RECORD_MIN_TIME;//最小录制时长，默认2S
    private boolean isRecording = false;//是否正在录制视频
    private boolean isStop = false;//是否停止过了MediaRecorder
    private int currentTime;
    private MediaRecorder mMediaRecorder;

    private Button btn;

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        //全屏模式
        requestWindowFeature(Window.FEATURE_NO_TITLE);
        getWindow().setFlags(WindowManager.LayoutParams.FLAG_FULLSCREEN, WindowManager.LayoutParams.FLAG_FULLSCREEN);
        //透明导航栏
        getWindow().addFlags(WindowManager.LayoutParams.FLAG_TRANSLUCENT_NAVIGATION);
        setContentView(R.layout.activity_camera);

        initViews();
        initTextureView();
    }

    //初始化TextureView
    private void initTextureView() {
        mCameraThread = new HandlerThread("CameraThread");
        mCameraThread.start();
        mCameraHandler = new Handler(mCameraThread.getLooper());
        mTextureView.setSurfaceTextureListener(this);
    }

    //初始化视图控件
    private void initViews() {
        mTextureView = findViewById(R.id.textureView);
        btn = findViewById(R.id.button);
        btn.setOnClickListener(clickListener);
        /*tvBalanceTime = findViewById(R.id.tv_balanceTime);
        ivTakePhoto = findViewById(R.id.iv_takePhoto);
        ivSwitchCamera = findViewById(R.id.iv_switchCamera);
        ivLightOn = findViewById(R.id.iv_lightOn);
        ivClose = findViewById(R.id.iv_close);
        mProgressView = findViewById(R.id.progressView);

        ivSwitchCamera.setOnClickListener(clickListener);
        ivLightOn.setOnClickListener(clickListener);
        ivClose.setOnClickListener(clickListener);

        //触摸事件
        onTouchListner();*/
    }

    View.OnClickListener clickListener = new View.OnClickListener() {
        @Override
        public void onClick(View view) {
            int i = view.getId();
            if (i == R.id.button) {
                if (!isRecording) {
                    prepareMediaRecorder();
                    startMediaRecorder();//开始录制
                    Toast.makeText(CameraActivity.this, "开始录制", Toast.LENGTH_LONG);
                } else {
                    stopMediaRecorder();
                    Toast.makeText(CameraActivity.this, "结束录制", Toast.LENGTH_LONG);
                }
                isRecording ^= true;
            }
        }
    };

    //开始录像
    private void startMediaRecorder() {
        Log.e("daasddasd", "startMediaRecorder");
        // Start recording
        try {
            mMediaRecorder.start();
            //开始计时，判断是否已经超过录制时间了
            isStop = false;
        } catch (Exception e) {
            e.printStackTrace();
        }
    }

    //停止录像
    private void stopMediaRecorder() {
        if (TextUtils.isEmpty(videoSavePath)) {
            return;
        }
        try {
            mMediaRecorder.stop();
            mMediaRecorder.reset();
            isStop = true;

            //录制完成后重置录制界面
            showResetCameraLayout();

        } catch (Exception e) {
            //这里抛出的异常是由于MediaRecorder开关时间过于短暂导致，直接按照录制时间短处理
            Toast.makeText(this, "录制时间过短", Toast.LENGTH_LONG).show();
            showResetCameraLayout();
        }

        currentTime = 0;
    }

    public void showResetCameraLayout() {
        resetCamera();
    }

    //重新配置打开相机
    public void resetCamera() {
        if (TextUtils.isEmpty(mCameraId)) {
            return;
        }

        if (mCameraDevice != null) {
            mCameraDevice.close();
        }

        setupCamera(width, height);
        openCamera(mCameraIdFront);
    }

    /**
     * ********************************************录像*********************************************
     */
    private void setUpMediaRecorder() {
        try {
            Log.e("daasddasd", "setUpMediaRecorder");
            mMediaRecorder.reset();
            mMediaRecorder.setAudioSource(MediaRecorder.AudioSource.MIC);
            mMediaRecorder.setVideoSource(MediaRecorder.VideoSource.SURFACE);
            // 这里有点投机取巧的方式，不过证明方法也是不错的
            // 录制出来10S的视频，大概1.2M，清晰度不错，而且避免了因为手动设置参数导致无法录制的情况
            // 手机一般都有这个格式CamcorderProfile.QUALITY_480P,因为单单录制480P的视频还是很大的，所以我们在手动根据预览尺寸配置一下videoBitRate,值越高越大
            // QUALITY_QVGA清晰度一般，不过视频很小，一般10S才几百K
            // 判断有没有这个手机有没有这个参数
            if (CamcorderProfile.hasProfile(CamcorderProfile.QUALITY_1080P)) {
                CamcorderProfile profile = CamcorderProfile.get(CamcorderProfile.QUALITY_1080P);
                profile.videoBitRate = mPreviewSize.getWidth() * mPreviewSize.getHeight();
                mMediaRecorder.setProfile(profile);
                mMediaRecorder.setPreviewDisplay(new Surface(mTextureView.getSurfaceTexture()));
            } else if (CamcorderProfile.hasProfile(CamcorderProfile.QUALITY_480P)) {
                CamcorderProfile profile = CamcorderProfile.get(CamcorderProfile.QUALITY_480P);
                profile.videoBitRate = mPreviewSize.getWidth() * mPreviewSize.getHeight();
                mMediaRecorder.setProfile(profile);
                mMediaRecorder.setPreviewDisplay(new Surface(mTextureView.getSurfaceTexture()));
            } else if (CamcorderProfile.hasProfile(CamcorderProfile.QUALITY_720P)) {
                CamcorderProfile profile = CamcorderProfile.get(CamcorderProfile.QUALITY_720P);
                profile.videoBitRate = mPreviewSize.getWidth() * mPreviewSize.getHeight();

                mMediaRecorder.setProfile(profile);
                mMediaRecorder.setPreviewDisplay(new Surface(mTextureView.getSurfaceTexture()));
            } else if (CamcorderProfile.hasProfile(CamcorderProfile.QUALITY_QVGA)) {
                mMediaRecorder.setProfile(CamcorderProfile.get(CamcorderProfile.QUALITY_QVGA));
                mMediaRecorder.setPreviewDisplay(new Surface(mTextureView.getSurfaceTexture()));
            } else if (CamcorderProfile.hasProfile(CamcorderProfile.QUALITY_CIF)) {
                mMediaRecorder.setProfile(CamcorderProfile.get(CamcorderProfile.QUALITY_CIF));
                mMediaRecorder.setPreviewDisplay(new Surface(mTextureView.getSurfaceTexture()));
            } else {
                mMediaRecorder.setOutputFormat(MediaRecorder.OutputFormat.MPEG_4);
                mMediaRecorder.setVideoEncoder(MediaRecorder.VideoEncoder.H264);
                mMediaRecorder.setAudioEncoder(MediaRecorder.AudioEncoder.AAC);
                mMediaRecorder.setVideoEncodingBitRate(10000000);
                mMediaRecorder.setVideoFrameRate(30);
                mMediaRecorder.setVideoEncodingBitRate(2500000);
                mMediaRecorder.setVideoFrameRate(20);
                mMediaRecorder.setVideoSize(mPreviewSize.getWidth(), mPreviewSize.getHeight());
            }

            //判断有没有配置过视频地址了
            Camera2Util.createSavePath(Camera2Config.PATH_SAVE_VIDEO);//判断有没有这个文件夹，没有的话需要创建
            String timeStamp = new SimpleDateFormat("yyyyMMdd_HHmmss").format(new Date());
            videoSavePath = Camera2Config.PATH_SAVE_VIDEO + "VIDEO_" + timeStamp + ".mp4";
            mMediaRecorder.setOutputFile(videoSavePath);

            //判断是不是前置摄像头,是的话需要旋转对应的角度
            if (isCameraFront) {
                mMediaRecorder.setOrientationHint(270);
            } else {
                mMediaRecorder.setOrientationHint(90);
            }
            mMediaRecorder.prepare();
        } catch (Exception e) {
            e.printStackTrace();
        }
    }

    //预览录像
    private void prepareMediaRecorder() {
        if (null == mCameraDevice || !mTextureView.isAvailable() || null == mPreviewSize) {
            return;
        }

        try {
            closePreviewSession();
            Log.e("aasdasdasd", "prepareMediaRecorder");
            setUpMediaRecorder();

            SurfaceTexture texture = mTextureView.getSurfaceTexture();
            assert texture != null;
            texture.setDefaultBufferSize(mPreviewSize.getWidth(), mPreviewSize.getHeight());
            mPreviewBuilder = mCameraDevice.createCaptureRequest(CameraDevice.TEMPLATE_RECORD);
            List<Surface> surfaces = new ArrayList<>();

            // Set up Surface for the camera preview
            Surface previewSurface = new Surface(texture);
            surfaces.add(previewSurface);
            mPreviewBuilder.addTarget(previewSurface);

            // Set up Surface for the MediaRecorder
            Surface recorderSurface = mMediaRecorder.getSurface();
            surfaces.add(recorderSurface);
            mPreviewBuilder.addTarget(recorderSurface);

            //判断预览之前有没有开闪光灯
            if (isLightOn) {
                mPreviewBuilder.set(CaptureRequest.FLASH_MODE, CaptureRequest.FLASH_MODE_TORCH);
            } else {
                mPreviewBuilder.set(CaptureRequest.FLASH_MODE, CaptureRequest.FLASH_MODE_OFF);
            }

            //保持当前的缩放比例
            //mPreviewBuilder.set(CaptureRequest.SCALER_CROP_REGION, zoom);

            mCameraDevice.createCaptureSession(surfaces, new CameraCaptureSession.StateCallback() {
                @Override
                public void onConfigured(CameraCaptureSession session) {
                    try {
                        //创建捕获请求
                        mCaptureRequest = mPreviewBuilder.build();
                        mPreviewSession = session;
                        //设置反复捕获数据的请求，这样预览界面就会一直有数据显示
                        mPreviewSession.setRepeatingRequest(mCaptureRequest, null, mCameraHandler);
                    } catch (Exception e) {
                        e.printStackTrace();
                        Log.e("dasdasdasdas", "捕获的异常2" + e.toString());
                    }
                }

                @Override
                public void onConfigureFailed(CameraCaptureSession session) {
                    Toast.makeText(getBaseContext(), "onConfigureFailed", Toast.LENGTH_SHORT).show();
                }
            }, null);
        } catch (Exception e) {
            e.printStackTrace();
        }
    }

    /**
     * ******************************SurfaceTextureListener*****************************************
     */
    @Override
    public void onSurfaceTextureAvailable(SurfaceTexture surfaceTexture, int width, int height) {
        //当SurefaceTexture可用的时候，设置相机参数并打开相机
        this.width = width;
        this.height = height;

        setupCamera(width, height);//配置相机参数
        openCamera(mCameraIdFront);//打开相机
    }

    @Override
    public void onSurfaceTextureSizeChanged(SurfaceTexture surface, int width, int height) {
        configureTransform(width, height);
    }

    @Override
    public boolean onSurfaceTextureDestroyed(SurfaceTexture surface) {
        return false;
    }

    @Override
    public void onSurfaceTextureUpdated(SurfaceTexture surface) {

    }

    /**
     * ******************************SetupCamera(配置Camera)*****************************************
     */
    private void setupCamera(int width, int height) {
        //获取摄像头的管理者CameraManager
        CameraManager manager = (CameraManager) getSystemService(Context.CAMERA_SERVICE);
        try {
            //0表示后置摄像头,1表示前置摄像头
            mCameraId = manager.getCameraIdList()[0];
            mCameraIdFront = manager.getCameraIdList()[1];

            //前置摄像头和后置摄像头的参数属性不同，所以这里要做下判断
            if (isCameraFront) {
                characteristics = manager.getCameraCharacteristics(mCameraIdFront);
            } else {
                characteristics = manager.getCameraCharacteristics(mCameraId);
            }

            //获取StreamConfigurationMap，它是管理摄像头支持的所有输出格式和尺寸
            StreamConfigurationMap map = characteristics.get(CameraCharacteristics.SCALER_STREAM_CONFIGURATION_MAP);
            mSensorOrientation = characteristics.get(CameraCharacteristics.SENSOR_ORIENTATION);
            //选择预览尺寸
            mPreviewSize = Camera2Util.getMinPreSize(map.getOutputSizes(SurfaceTexture.class), width, height, Camera2Config.PREVIEW_MAX_HEIGHT);

            Log.e(TAG, mPreviewSize.getWidth() + "----" + mPreviewSize.getHeight());
            Log.e(TAG, height + "----" + width);

            //获取相机支持的最大拍照尺寸
            mCaptureSize = Collections.max(Arrays.asList(map.getOutputSizes(ImageFormat.JPEG)), new Comparator<Size>() {
                @Override
                public int compare(Size lhs, Size rhs) {
                    return Long.signum(lhs.getWidth() * lhs.getHeight() - rhs.getHeight() * rhs.getWidth());
                }
            });

            configureTransform(width, height);

            //此ImageReader用于拍照所需
            setupImageReader();

            //MediaRecorder用于录像所需
            mMediaRecorder = new MediaRecorder();
        } catch (Exception e) {
            e.printStackTrace();
        }
    }

    //配置ImageReader
    private void setupImageReader() {
        //2代表ImageReader中最多可以获取两帧图像流
        mImageReader = ImageReader.newInstance(mCaptureSize.getWidth(), mCaptureSize.getHeight(),
                ImageFormat.JPEG, 2);
        mImageReader.setOnImageAvailableListener(new ImageReader.OnImageAvailableListener() {
            @Override
            public void onImageAvailable(ImageReader reader) {
                Image mImage = reader.acquireNextImage();
                ByteBuffer buffer = mImage.getPlanes()[0].getBuffer();
                byte[] data = new byte[buffer.remaining()];
                buffer.get(data);
                String timeStamp = new SimpleDateFormat("yyyyMMdd_HHmmss").format(new Date());
                Camera2Util.createSavePath(Camera2Config.PATH_SAVE_PIC);//判断有没有这个文件夹，没有的话需要创建
                picSavePath = Camera2Config.PATH_SAVE_PIC + "IMG_" + timeStamp + ".jpg";
                FileOutputStream fos = null;
                try {
                    fos = new FileOutputStream(picSavePath);
                    fos.write(data, 0, data.length);

                    Message msg = new Message();
                    msg.what = CAPTURE_OK;
                    msg.obj = picSavePath;
                    mCameraHandler.sendMessage(msg);
                } catch (IOException e) {
                    e.printStackTrace();
                } finally {
                    if (fos != null) {
                        try {
                            fos.close();
                        } catch (IOException e) {
                            e.printStackTrace();
                        }
                    }
                }
                mImage.close();
            }
        }, mCameraHandler);

        mCameraHandler = new Handler() {
            @Override
            public void handleMessage(Message msg) {
                super.handleMessage(msg);
                switch (msg.what) {
                    case CAPTURE_OK:
                        //这里拍照保存完成，可以进行相关的操作，例如再次压缩等(由于封装，这里我先跳转掉完成页面)
                        /*if (Camera2Config.ACTIVITY_AFTER_CAPTURE != null) {
                            Intent intent = new Intent(Camera2RecordActivity.this, Camera2Config.ACTIVITY_AFTER_CAPTURE);
                            intent.putExtra(Camera2Config.INTENT_PATH_SAVE_PIC, picSavePath);
                            startActivity(intent);
                        }*/
                        break;
                }
            }
        };
    }

    /**
     * 屏幕方向发生改变时调用转换数据方法
     *
     * @param viewWidth  mTextureView 的宽度
     * @param viewHeight mTextureView 的高度
     */
    private void configureTransform(int viewWidth, int viewHeight) {
        if (null == mTextureView || null == mPreviewSize) {
            return;
        }
        int rotation = getWindowManager().getDefaultDisplay().getRotation();
        Matrix matrix = new Matrix();
        RectF viewRect = new RectF(0, 0, viewWidth, viewHeight);
        RectF bufferRect = new RectF(0, 0, mPreviewSize.getHeight(), mPreviewSize.getWidth());
        float centerX = viewRect.centerX();
        float centerY = viewRect.centerY();
        if (Surface.ROTATION_90 == rotation || Surface.ROTATION_270 == rotation) {
            bufferRect.offset(centerX - bufferRect.centerX(), centerY - bufferRect.centerY());
            matrix.setRectToRect(viewRect, bufferRect, Matrix.ScaleToFit.FILL);
            float scale = Math.max(
                    (float) viewHeight / mPreviewSize.getHeight(),
                    (float) viewWidth / mPreviewSize.getWidth());
            matrix.postScale(scale, scale, centerX, centerY);
            matrix.postRotate(90 * (rotation - 2), centerX, centerY);
        }
        mTextureView.setTransform(matrix);
    }

    /**
     * ******************************openCamera(打开Camera)*****************************************
     */
    private void openCamera(String CameraId) {
        //获取摄像头的管理者CameraManager
        CameraManager manager = (CameraManager) getSystemService(Context.CAMERA_SERVICE);
        //检查权限
        try {
            if (ActivityCompat.checkSelfPermission(this, Manifest.permission.CAMERA) != PackageManager.PERMISSION_GRANTED) {
                return;
            }
            //打开相机，第一个参数指示打开哪个摄像头，第二个参数stateCallback为相机的状态回调接口，第三个参数用来确定Callback在哪个线程执行，为null的话就在当前线程执行
            manager.openCamera(CameraId, mStateCallback, null);
        } catch (CameraAccessException e) {
            e.printStackTrace();
        }
    }

    private CameraDevice.StateCallback mStateCallback = new CameraDevice.StateCallback() {
        @Override
        public void onOpened(CameraDevice camera) {
            mCameraDevice = camera;
            startPreview();

            if (null != mTextureView) {
                configureTransform(mTextureView.getWidth(), mTextureView.getHeight());
            }
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

    /**
     * ******************************Camera2成功打开，开始预览(startPreview)*************************
     */
    public void startPreview() {
        if (null == mCameraDevice || !mTextureView.isAvailable() || null == mPreviewSize) {
            return;
        }

        SurfaceTexture mSurfaceTexture = mTextureView.getSurfaceTexture();//获取TextureView的SurfaceTexture，作为预览输出载体

        if (mSurfaceTexture == null) {
            return;
        }

        try {
            closePreviewSession();
            mSurfaceTexture.setDefaultBufferSize(mPreviewSize.getWidth(), mPreviewSize.getHeight());//设置TextureView的缓冲区大小
            mPreviewBuilder = mCameraDevice.createCaptureRequest(CameraDevice.TEMPLATE_PREVIEW);//创建CaptureRequestBuilder，TEMPLATE_PREVIEW比表示预览请求
            Surface mSurface = new Surface(mSurfaceTexture);//获取Surface显示预览数据
            mPreviewBuilder.addTarget(mSurface);//设置Surface作为预览数据的显示界面

            //默认预览不开启闪光灯
            mPreviewBuilder.set(CaptureRequest.FLASH_MODE, CaptureRequest.FLASH_MODE_OFF);

            //创建相机捕获会话，第一个参数是捕获数据的输出Surface列表，第二个参数是CameraCaptureSession的状态回调接口，当它创建好后会回调onConfigured方法，第三个参数用来确定Callback在哪个线程执行，为null的话就在当前线程执行
            mCameraDevice.createCaptureSession(Arrays.asList(mSurface, mImageReader.getSurface()), new CameraCaptureSession.StateCallback() {
                @Override
                public void onConfigured(CameraCaptureSession session) {
                    try {
                        //创建捕获请求
                        mCaptureRequest = mPreviewBuilder.build();
                        mPreviewSession = session;
                        //不停的发送获取图像请求，完成连续预览
                        mPreviewSession.setRepeatingRequest(mCaptureRequest, null, mCameraHandler);
                    } catch (Exception e) {
                        e.printStackTrace();
                    }
                }

                @Override
                public void onConfigureFailed(CameraCaptureSession session) {

                }
            }, null);
        } catch (Exception e) {
            e.printStackTrace();
            Log.e("dasdadasd", "捕获的异常" + e.toString());
        }
    }

    //清除预览Session
    private void closePreviewSession() {
        if (mPreviewSession != null) {
            mPreviewSession.close();
            mPreviewSession = null;
        }
    }


}
