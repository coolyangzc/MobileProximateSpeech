//
// Created by coolyangzc on 12/28/2018.
//

#include <jni.h>
#include <string>
#include <stdlib.h>
#include <dlfcn.h>
#include <android/log.h>
#include <sys/types.h>
#include <sys/stat.h>
#include <fcntl.h>
#include <unistd.h>
#include <pthread.h>
#include <sys/epoll.h>
#include <string.h>
#define TS_ROI_DATA_FILE "/sys/touchscreen/roi_data_internal"
#define TS_DIFF_FILE  "/data/diff_data"
#define TS_READ 0
#define TS_WRITE 1
#define  TAG "READ_DIFF"

#define LOGD(...)  __android_log_print(ANDROID_LOG_DEBUG, TAG, __VA_ARGS__)
#define LOGE(...)  __android_log_print(ANDROID_LOG_ERROR, TAG, __VA_ARGS__)

#define DIFF_LENGTH  32*18
#define MAXLINE 2048



struct FalseTouchData{
    int x;
    int y;
    int id;
};
struct FalseFrameData{
    int16_t diffData[32*18];
    uint16_t rawData[32*18];
    int touchNum;
    int downNum;
    struct FalseTouchData touchData[10];
};



jmethodID callBack_method;
pthread_t thread_1;
JavaVM* g_jvm;
int pipefd[2] = {-1,-1};

void *run(void *args){
    JNIEnv *env;
    int timeoutMs = 120;//120ms
    int status  = g_jvm->GetEnv((void **)&env, JNI_VERSION_1_6);
    if(status < 0){
        status = g_jvm->AttachCurrentThread(&env, NULL);
        if(status < 0){
            env = NULL;
            LOGD("get Env Failed..");
            return NULL;
        }
    }



    jshortArray diffdata = env->NewShortArray(DIFF_LENGTH);
    jshortArray rawdata = env->NewShortArray(DIFF_LENGTH);
    //jshort * data_ = env->GetShortArrayElements(data,NULL);
    short buf[MAXLINE] = {0};
    LOGD("Thread Coming...");
    //env->SetIntArrayRegion(data,0,DIFF_LENGTH,data_);

    int epfd,nfds,fd,recvNum,sockfd;
    struct epoll_event ev,events[20];
    struct timeval tv;
    epfd = epoll_create(10);
    fd  = open(TS_DIFF_FILE,O_RDONLY | O_NONBLOCK);
    if(fd < 0){
        LOGE("open diff_data Error");
        return NULL;
    }
    ev.data.fd=fd;
    ev.events = EPOLLIN;
    epoll_ctl(epfd,EPOLL_CTL_ADD,fd,&ev);

    if(pipe(pipefd) < 0){
        LOGE("pipe Error");
        close(fd);
        return NULL;
    }
    ev.data.fd = pipefd[0];
    ev.events = EPOLLIN;
    epoll_ctl(epfd,EPOLL_CTL_ADD,pipefd[0],&ev);
    int ret = fcntl(pipefd[0],F_SETFL,(fcntl(pipefd[0],F_GETFL) | O_NONBLOCK));
    if(ret < 0){
        LOGE("fcntl pipefd Error");
        return  NULL;
    }
    while(1)
    {
        nfds=epoll_wait(epfd,events,5,timeoutMs);
        if(nfds == 0){
            continue; //超时
        }

        for(int i=0;i<nfds;++i)
        {
            if(events[i].events & EPOLLIN)//
            {
                if ((sockfd = events[i].data.fd) < 0)
                    continue;
                if(sockfd == fd)  //diffData
                {
                    gettimeofday(&tv,NULL);
                    struct FalseFrameData frameData;
                    memset(&frameData,0, sizeof(frameData));
                    recvNum = read(sockfd, (char *)&frameData, sizeof(frameData));
                    //memset(buf,0,MAXLINE*sizeof(short));
                    //recvNum = read(sockfd, (char *)buf,MAXLINE);
                    if(recvNum < 0){
                        LOGE("Read Eroor");
                        break;
                    }else if(recvNum !=  sizeof(frameData)){
                        LOGE("frameData  InComplete !!!");
                        break;
                    }
                    long t = tv.tv_sec * 1000 + tv.tv_usec / 1000;
                    LOGD("Time:%ld %ld %ld TouchNum:%d  DownNum:%d",tv.tv_sec, tv.tv_usec,t,frameData.touchNum,frameData.downNum);
                    for(int i = 0; i <frameData.touchNum;i++){
                        LOGD("ID:%d  x:%d  y:%d",frameData.touchData[i].id,frameData.touchData[i].x,frameData.touchData[i].y);
                    }


                    env->SetShortArrayRegion(diffdata,0,DIFF_LENGTH,frameData.diffData);
                   // env->SetShortArrayRegion(rawdata,0,DIFF_LENGTH,(jshort*)frameData.rawData);//回调java处理函数
                    env->CallVoidMethod((jobject)args,callBack_method,diffdata,t);
                }else{  //app exit
                    char buf[10];
                    read(sockfd,buf,10);
                    LOGD("Read Diff exit------------");
                    close(pipefd[0]);
                    close(pipefd[1]);
                    close(fd);
                    env->DeleteGlobalRef((jobject)args);
                    return NULL;
                }
            }
        }
    }
}



extern "C"
JNIEXPORT void JNICALL
Java_com_yzc_proximatespeechrecorder_CapacityActivity_readDiffStart(JNIEnv *env, jobject instance) {


/*
    jclass cla = (env)->FindClass("com/example/diffshow/MainActivity");
    if(cla == 0){
        __android_log_print(ANDROID_LOG_DEBUG,TAG,"find class error");
        return ;
    }
    LOGD("Find Class...");
*/


    env->GetJavaVM(&g_jvm); // 保存java虚拟机对象
    callBack_method = env->GetMethodID(env->GetObjectClass(instance),"processDiff","([S)V");

    if(callBack_method == 0){
        __android_log_print(ANDROID_LOG_DEBUG,TAG,"find callBack_method error");
        return ;
    }
    LOGD("Find Func...");
    jobject obj = env->NewGlobalRef(instance);
    pthread_create(&thread_1, NULL, run, obj);
    LOGD("readDiffStart...");
}



extern "C"
JNIEXPORT void JNICALL
Java_com_yzc_proximatespeechrecorder_CapacityActivity_readDiffStop(JNIEnv *env, jobject instance) {

    // TODO
    if(pipefd[1] < 0)
        return;
    write(pipefd[1],"1",1);
    LOGD("readDiffStop...");
}



extern "C"
JNIEXPORT void JNICALL
Java_com_yzc_proximatespeechrecorder_SensorActivity_readDiffStart(JNIEnv *env, jobject instance) {

    env->GetJavaVM(&g_jvm); // 保存java虚拟机对象
    callBack_method = env->GetMethodID(env->GetObjectClass(instance),"processCapa","([SJ)V");

    if(callBack_method == 0){
        __android_log_print(ANDROID_LOG_DEBUG,TAG,"find callBack_method error");
        return ;
    }
    LOGD("Find Func...");
    jobject obj = env->NewGlobalRef(instance);
    pthread_create(&thread_1, NULL, run, obj);
    LOGD("readDiffStart...");
}



extern "C"
JNIEXPORT void JNICALL
Java_com_yzc_proximatespeechrecorder_SensorActivity_readDiffStop(JNIEnv *env, jobject instance) {

    // TODO
    if(pipefd[1] < 0)
        return;
    write(pipefd[1],"1",1);
    LOGD("readDiffStop...");
}