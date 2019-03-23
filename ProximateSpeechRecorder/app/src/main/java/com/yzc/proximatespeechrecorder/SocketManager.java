package com.yzc.proximatespeechrecorder;

import android.util.Log;

import java.io.IOException;
import java.io.InputStream;
import java.io.OutputStream;
import java.net.ServerSocket;
import java.net.Socket;
import java.util.concurrent.ExecutorService;
import java.util.concurrent.Executors;

public class SocketManager {

    private final String HOST = "192.168.1.102";
    private final int MOTION_PORT = 8888;
    private final int IMG_PORT = 8889;
    private final int RECV_PORT = 8890;
    private static SocketManager shared = new SocketManager();
    public static SocketManager getInstance() { return shared; }

    private Socket motion_socket, img_socket, recv_socket;

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

        mThreadPool.execute(new Runnable() {
            @Override
            public void run() {
                try {
                    while (motion_socket==null)
                        Thread.sleep(100);
                    InputStream is = motion_socket.getInputStream();
                    byte buffer[] = new byte[128];
                    int temp;
                    while ((temp = is.read(buffer)) != -1)
                        Log.d("RECV", new String(buffer, 0, temp));
                } catch (IOException e) {
                    e.printStackTrace();
                } catch (InterruptedException e) {
                    e.printStackTrace();
                }

            }
        });

        /*mThreadPool.execute(new Runnable() {
            @Override
            public void run() {
                try {
                    recv_socket = new Socket(HOST, RECV_PORT);
                    InputStream is = recv_socket.getInputStream();
                    byte buffer[] = new byte[128];
                    int temp;
                    while (true) {
                        while ((temp = is.read(buffer)) != -1) {
                            Log.d("RECV", new String(buffer, 0, temp));
                        }
                    }
                } catch (IOException e) {
                    e.printStackTrace();
                }
            }
        });*/
    }

    public boolean isConnected() {
        return motion_socket != null && motion_socket.isConnected();
    }

    public static byte[] intToByteArray(int a) {
        return new byte[] {
                (byte) ((a >> 24) & 0xFF),
                (byte) ((a >> 16) & 0xFF),
                (byte) ((a >> 8) & 0xFF),
                (byte) (a & 0xFF)
        };
    }

    public void send_img(byte[] bytes) {
        final byte[] byteArray = bytes;
        mThreadPool.execute(new Runnable() {
            @Override
            public void run() {
                try {
                    OutputStream os = img_socket.getOutputStream();
                    Log.d("SocketManager", "pic len: " + String.valueOf(byteArray.length));
                    os.write(intToByteArray(byteArray.length));
                    os.write(byteArray);
                    os.flush();

                    /*InputStream is = img_socket.getInputStream();
                    byte buffer[] = new byte[128];
                    int temp;
                    while ((temp = is.read(buffer)) != -1) {
                        Log.d("RECV", new String(buffer, 0, temp));
                    }*/
                } catch (IOException e) {
                    e.printStackTrace();
                }

            }
        });
    }

    public void send_motion(String msg) {
        final String str = msg;

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
