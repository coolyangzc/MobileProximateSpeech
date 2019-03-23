package com.yzc.proximatespeechrecorder;

import android.util.Log;

import java.io.IOException;
import java.io.OutputStream;
import java.net.Socket;
import java.util.concurrent.ExecutorService;
import java.util.concurrent.Executors;

public class SocketManager {

    private final String HOST = "192.168.1.102";
    private final int MOTION_PORT = 8888;
    private final int IMG_PORT = 8889;
    private static SocketManager shared = new SocketManager();
    public static SocketManager getInstance() { return shared; }

    private Socket motion_socket, img_socket;

    private ExecutorService mThreadPool;

    OutputStream os;

    private SocketManager() {
        mThreadPool = Executors.newCachedThreadPool();
    }

    public void connect() {
        mThreadPool.execute(new Runnable() {
            @Override
            public void run() {
                try {
                    motion_socket = new Socket(HOST, MOTION_PORT);
                    img_socket = new Socket(HOST, IMG_PORT);
                    Log.d("Socket", String.valueOf(motion_socket.isConnected()));
                } catch (IOException e) {
                    Log.d("Socket","Socket can't used");
                    e.printStackTrace();
                }
            }

        });
    }

    public boolean isConnected() {
        return motion_socket != null && motion_socket.isConnected();
    }

    public void send_img() {

    }

    public void send_motion(String msg) {
        final String str = msg;

        // 利用线程池直接开启一个线程 & 执行该线程
        mThreadPool.execute(new Runnable() {
            @Override
            public void run() {
                try {
                    os = motion_socket.getOutputStream();
                    os.write(str.getBytes("utf-8"));
                    os.flush();
                } catch (IOException e) {
                    e.printStackTrace();
                }

            }
        });
    }
}
