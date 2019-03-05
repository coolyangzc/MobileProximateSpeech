# 声音数据预处理说明

2019年03月05日

郑逢时

[TOC]

以下0. 1.均为手动操作

## 0. 数据导入

通过adb将实验数据（`.mp4`，`.txt`）文件移动到`Analysis/Data/Study3/subjects/xxx/original`文件夹，xxx是受试者的名字。

## 1. MP4到WAV的格式转换

使用Adobe Audition软件的Batch Export功能，将`Analysis/Data/Study3/subjects/xxx`下的所有MP4文件转化为WAV格式，导出设置中参数为：

![image-20190305143851249](/Users/james/MobileProximateSpeech/Analysis/utils/voice_preprocess/assets/image-20190305143851249.png)

注意只有这种参数的WAV文件才能被后续的`Pydub`、`VAD`等包所识别。

------

以下均为Python操作，若要图方便，可以直接打开`utils.voice_preprocess.lazy`，修改受试者名字后，一键运行。

![image-20190305152730157](/Users/james/MobileProximateSpeech/Analysis/utils/voice_preprocess/assets/image-20190305152730157.png)

## 2. 数据过滤

为了过滤掉实验中失败的录音和记录，调用`utils.raw_data_filter`的`filter3`函数：

```python
filter3('../Data/Study3/subjects/xxx/original', deal_individual=True, audio_format='wav')
```

该函数会自动创建同级目录`Data/Study3/subjects/xxx/filtered/`，目录内是过滤好的 .wav 和 .txt 文件

## 3. 音频修剪

每次实验从用户按下开始按钮开始录制音频，但有用的只是手机振动信号结束后的部分。因此我们需要对.wav音频进行修剪。

为此，调用`utils.voice_preprocess.voice_trimmer`的`trim_in_dir`函数：

```python
trim_in_dir('Data/Study3/subjects/xxx/filtered/', in_format='wav', out_format='wav')
```

该函数会自动创建同级目录`Data/Study3/subjects/xxx/trimmed/`，目录内是修剪好的 .wav 文件

## 4. 人声过滤

调用`utils.voice_preprocess.VAD`的`get_voice_chunks_in_dir`函数，对`trimmed/`目录下的 .wav 文件进行人声块的识别与过滤

```python
get_voice_chunks_in_dir('Data/Study3/subjects/xxx/trimmed', aggressiveness=3)
```

其中`aggressiveness`的值取1, 2, 3，值越高，对noise的容忍度越低，建议取3

该函数会自动在`/trimmed`文件夹下以试验时间为名创建很多子文件夹，每次实验对应一个文件夹，每个文件夹下是该实验wav文件被人声识别后分割成的片段，每个片段里面都基本上是人声了。有时候文件夹为空，这是因为该实验人声太小了，或者噪音太大，无法识别（比如裤兜小声）。

