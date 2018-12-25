package com.yzc.proximatespeechrecorder;

import android.Manifest;
import android.app.Activity;
import android.content.Context;
import android.content.pm.PackageManager;
import android.graphics.SurfaceTexture;
import android.hardware.camera2.CameraAccessException;
import android.hardware.camera2.CameraCaptureSession;
import android.hardware.camera2.CameraCharacteristics;
import android.hardware.camera2.CameraDevice;
import android.hardware.camera2.CameraManager;
import android.hardware.camera2.CaptureRequest;
import android.hardware.camera2.params.StreamConfigurationMap;
import android.media.CamcorderProfile;
import android.media.MediaRecorder;
import android.os.Bundle;
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

import java.text.SimpleDateFormat;
import java.util.ArrayList;
import java.util.Date;
import java.util.List;

public class CameraActivity extends Activity implements TextureView.SurfaceTextureListener {

    //constant
    private static final String TAG = "Camera2RecordActivity";
    private String mCameraId;//后置摄像头ID
    private String mCameraIdFront;//前置摄像头ID
    private Size mPreviewSize;//预览的Size
    private int width = 1080;//TextureView的宽
    private int height = 1920;//TextureView的高
    private boolean isCameraFront = true;//当前是否是前置摄像头

    //Camera2
    private CameraDevice mCameraDevice;
    private CaptureRequest.Builder mPreviewBuilder;
    private CaptureRequest mCaptureRequest;
    private CameraCaptureSession mPreviewSession;
    private CameraCharacteristics characteristics;
    private String videoSavePath;//视频保存路径

    //handler
    private TextureView mTextureView;

    //录像
    private boolean isRecording = false;//是否正在录制视频
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
        setupCamera(width, height);//配置相机参数
        openCamera(mCameraIdFront);//打开相机
    }

    //初始化视图控件
    private void initViews() {
        mTextureView = findViewById(R.id.textureView);
        btn = findViewById(R.id.button);
        btn.setOnClickListener(clickListener);
    }

    //初始化TextureView
    private void initTextureView() {
        mTextureView.setSurfaceTextureListener(this);
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

            //录制完成后重置录制界面
            showResetCameraLayout();

        } catch (Exception e) {
            //这里抛出的异常是由于MediaRecorder开关时间过于短暂导致，直接按照录制时间短处理
            Toast.makeText(this, "录制时间过短", Toast.LENGTH_LONG).show();
            showResetCameraLayout();
        }

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
                //profile.videoBitRate = mPreviewSize.getWidth() * mPreviewSize.getHeight();
                profile.videoBitRate = 1920 * 1080;
                mMediaRecorder.setProfile(profile);
                mMediaRecorder.setPreviewDisplay(new Surface(mTextureView.getSurfaceTexture()));
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
            //Surface previewSurface = new Surface(texture);
            //surfaces.add(previewSurface);
            //mPreviewBuilder.addTarget(previewSurface);

            // Set up Surface for the MediaRecorder
            Surface recorderSurface = mMediaRecorder.getSurface();
            surfaces.add(recorderSurface);
            mPreviewBuilder.addTarget(recorderSurface);


            mCameraDevice.createCaptureSession(surfaces, new CameraCaptureSession.StateCallback() {
                @Override
                public void onConfigured(CameraCaptureSession session) {
                    try {
                        //创建捕获请求
                        mCaptureRequest = mPreviewBuilder.build();
                        mPreviewSession = session;
                        //设置反复捕获数据的请求，这样预览界面就会一直有数据显示
                        mPreviewSession.setRepeatingRequest(mCaptureRequest, null, null);
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
    }

    @Override
    public void onSurfaceTextureSizeChanged(SurfaceTexture surface, int width, int height) {
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
            //选择预览尺寸
            mPreviewSize = Camera2Util.getMinPreSize(map.getOutputSizes(SurfaceTexture.class), width, height, Camera2Config.PREVIEW_MAX_HEIGHT);

            Log.e(TAG, mPreviewSize.getWidth() + "----" + mPreviewSize.getHeight());
            Log.e(TAG, height + "----" + width);

            //MediaRecorder用于录像所需
            mMediaRecorder = new MediaRecorder();
        } catch (Exception e) {
            e.printStackTrace();
        }
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

    //清除预览Session
    private void closePreviewSession() {
        if (mPreviewSession != null) {
            mPreviewSession.close();
            mPreviewSession = null;
        }
    }
}
