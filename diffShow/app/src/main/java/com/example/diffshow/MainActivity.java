package com.example.diffshow;

import android.app.Activity;
import android.graphics.Point;
import android.os.Handler;
import android.os.Message;
import android.os.Bundle;
import android.util.Log;
import android.view.MotionEvent;
import android.view.Window;
import android.view.WindowManager;
import android.widget.TextView;

public class MainActivity extends Activity {
    public  final String TAG = "READ_DIFF_JAVA";
    //TextView tv;
    short diffData[] = new short[32*18];
    CapacityView capacityView;
    int screenWidth;
    int screenHeight;
    // Used to load the 'native-lib' library on application startup.
    static {
        System.loadLibrary("native-lib");
    }

    private   Handler myHandler = new Handler(){
        @Override
        public void handleMessage(Message msg) {
            capacityView.invalidate();
        }
    };
    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        requestWindowFeature(Window.FEATURE_NO_TITLE);
        getWindow().setFlags(WindowManager.LayoutParams. FLAG_FULLSCREEN , WindowManager.LayoutParams. FLAG_FULLSCREEN);
        setContentView(R.layout.activity_main);
        capacityView = findViewById(R.id.capacityView);
        // Example of a call to a native method

        Point size = new Point();
        getWindowManager().getDefaultDisplay().getRealSize(size);
        screenWidth = size.x;
        screenHeight = size.y;
        capacityView.screenHeight = screenHeight;
        capacityView.screenWidth = screenWidth;
        capacityView.diffData = diffData;

        readDiffStart();
    }

    @Override
    protected void onDestroy() {
        super.onDestroy();
        readDiffStop();
    }

    @Override
    public boolean onTouchEvent(MotionEvent event) {
        int action = event.getActionMasked();
        if(action == MotionEvent.ACTION_DOWN || action == MotionEvent.ACTION_POINTER_DOWN){
            Log.d(TAG,"------  Down Point Id:"+event.getPointerId(event.getActionIndex()));
        }
        for(int i = 0; i<event.getPointerCount();++i){
            Log.d(TAG,"------  Id:"+event.getPointerId(i)+"  x:"+event.getX(i)+"  y:"+event.getY(i));
        }
        return super.onTouchEvent(event);
    }

    public void processDiff(short[] data){
        capacityView.diffData =  data;
        myHandler.obtainMessage(0).sendToTarget();
        //Log.d(TAG,"processDiff touchNum :"+data.touchNum);
    }
    /**
     * A native method that is implemented by the 'native-lib' native library,
     * which is packaged with this application.
     */
    public native void readDiffStart();
    public native void readDiffStop(); // Java_com_example_diffshow_MainActivity_readDiffStop
}
