package com.yzc.proximatespeechrecorder;

import android.util.Log;

import java.io.IOException;
import java.io.OutputStream;
import java.net.Socket;
import java.util.concurrent.ExecutorService;
import java.util.concurrent.Executors;

public class SocketManager {

    private final String HOST = "192.168.1.102";
    private final int PORT = 8888;
    private static SocketManager shared = new SocketManager();
    public static SocketManager getInstance() { return shared; }

    private Socket socket;

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
                    // 创建Socket对象 & 指定服务端的IP 及 端口号
                    socket = new Socket(HOST, PORT);


                    // 判断客户端和服务器是否连接成功
                    Log.d("Socket", String.valueOf(socket.isConnected()));
                } catch (IOException e) {
                    Log.d("Socket","Socket can't used");
                    e.printStackTrace();
                }
            }

        });
    }

    public boolean isConnected() {
        return socket != null && socket.isConnected();
    }

    public void send(String msg) {
        final String str = msg;

        // 利用线程池直接开启一个线程 & 执行该线程
        mThreadPool.execute(new Runnable() {
            @Override
            public void run() {
                try {
                    os = socket.getOutputStream();
                    os.write(str.getBytes("utf-8"));
                    os.flush();
                } catch (IOException e) {
                    e.printStackTrace();
                }

            }
        });
    }
}
