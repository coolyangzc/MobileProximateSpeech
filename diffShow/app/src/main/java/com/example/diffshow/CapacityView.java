package com.example.diffshow;

import android.content.Context;
import android.graphics.Canvas;
import android.graphics.Color;
import android.graphics.Paint;
import android.graphics.Rect;
import android.util.AttributeSet;
import android.view.MotionEvent;
import android.view.View;

/**
 * Created by dWX465903 on 2017/12/23.
 */


public class CapacityView extends View {

    final static int tpWidth = 18;
    final static int tpHeight = 32;

    int screenWidth;
    int screenHeight;

    float capWidth;
    float capHeight;

    short diffData[];

    Paint fillPaint[];
    Paint strokePaint;
    Paint textPaint;

    public CapacityView(Context context) {
        super(context);
        init();
    }

    public CapacityView(Context context, AttributeSet attrs) {
        super(context, attrs);
        init();
    }

    public CapacityView(Context context, AttributeSet attrs, int defStyle) {
        super(context, attrs, defStyle);
        init();
    }

    public void init() {
        diffData = new short[tpWidth * tpHeight];
        fillPaint = new Paint[tpWidth * tpHeight];
        for (int i = 0; i < fillPaint.length; ++i) {
            fillPaint[i] = new Paint();
            fillPaint[i].setStyle(Paint.Style.FILL_AND_STROKE);
            fillPaint[i].setColor(Color.GRAY);
        }

        strokePaint = new Paint();
        strokePaint.setStyle(Paint.Style.STROKE);
        strokePaint.setColor(Color.BLACK);
        textPaint = new Paint();
        textPaint.setStyle(Paint.Style.FILL_AND_STROKE);
        textPaint.setColor(Color.BLACK);
        textPaint.setTextSize(30);
    }


    public void setColor(int i){
        int maxVal = 2550;
        int minVal = 0;
        int r , g ,b;
        r = 255;
        g = 255;
        b = 255;
        if(diffData[i] > maxVal){
            g = 0;
        }else if (diffData[i] < minVal){
            r = 255;
            g = 255;
            b = 255;
            /*
            r = 205;
            g = 190;
            b = 112;
            */
        }else {
            int tmp =  (diffData[i]-minVal)*255/(maxVal-minVal);
            g = 255-tmp;
        }
        fillPaint[i].setColor(Color.rgb(r,g,b));
    }
    @Override
    protected void onDraw(Canvas canvas) {
        super.onDraw(canvas);

        capHeight = screenHeight / tpHeight;
        capWidth = screenWidth / tpWidth;


        for (int i = 0; i < tpWidth * tpHeight; ++i) {
            int capacityY = i / tpWidth;
            int capacityX = i % tpWidth;

            Rect rect = new Rect((int) (capacityX * capWidth), (int) (capacityY * capHeight), (int) ((capacityX + 1) * capWidth), (int) ((capacityY + 1) * capHeight));
            setColor(i);
            canvas.drawRect(rect, fillPaint[i]);
            canvas.drawRect(rect, strokePaint);
            canvas.drawText(""+diffData[i],(int) (capacityX * capWidth),(int) ((capacityY+0.7) * capHeight),textPaint);

        }
    }

    @Override
    public boolean dispatchTouchEvent(MotionEvent event) {
        invalidate();
        return super.dispatchTouchEvent(event);
    }
}