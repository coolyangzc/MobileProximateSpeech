package com.yzc.proximatespeechrecorder;

import android.util.Log;

import java.util.ArrayList;
import java.util.Arrays;
import java.util.Collections;
import java.util.List;
import java.util.Random;

public class Study1Task {

    private int task_id, repeat_times;
    private List<String> tasks = new ArrayList<>();
    private List<Integer> speechList = new ArrayList<>();
    private Random random;

    Study1Task(int seed) {
        random = new Random(seed);
        initTasks();
        task_id = repeat_times = 0;
    }

    private void initTasks() {
        List<String> pos = Arrays.asList(
                "竖直对脸，碰触鼻子",
                "竖直对脸，不碰鼻子",
                "竖屏握持，上端遮嘴",
                "水平端起，倒话筒"
        );
        List<String> start = Arrays.asList(
                "手中",
                "桌上"
        );
        List<String> user = Arrays.asList(
                "坐",
                "站"
        ); // do not random
        Collections.shuffle(pos, random);
        Collections.shuffle(start, random);
        for (String s : start)
            for (String p : pos)
                for (String u: user)
                    tasks.add(u + "\n" + s + "\n" + p);
        for (String u : user)
            tasks.add(u + "\n横屏" + "\n横屏遮嘴");
        for (String p: pos)
            tasks.add("站\n" + "裤兜\n" + p);

        List<String> lying = Arrays.asList(
                "平躺",
                "侧躺"
        );
        Collections.shuffle(lying, random);
        String l = lying.get(0) + "/" + lying.get(1) + "\n";
        for(String p: pos)
            tasks.add(l + "手中\n" + p);
        tasks.add(l + "横屏\n" + "横屏遮嘴");
        /*for (String l: lying) {
            for (String p : pos)
                tasks.add(l + "\n" + "手中\n" + p);
            tasks.add(l + "\n" + "横屏\n" + "横屏遮嘴");
        }*/
        for (String p : pos)
            tasks.add("走\n" + "手中\n" + p);

        List<String> negativeTasks = Arrays.asList(
                "坐\n手中\n打字",
                "坐\n手中\n浏览",
                "坐\n手中\n拍照",
                "坐\n手中\n接听"
        );
        Collections.shuffle(negativeTasks, random);
        tasks.addAll(negativeTasks);
        tasks.add("走\n裤兜\n裤兜");
        tasks.add("走\n手中\n手中");
        for (String t: tasks)
            Log.e("tasks", t);

        for(int i = 0; i < tasks.size() * 10; ++i)
            speechList.add(random.nextInt(commands.length));
    }

    public String startPosition[] = new String[] {
            "桌上（正面）",
            "桌上（反面）",
            "竖屏握持（正面）",
            "竖屏握持（反面）",
            "横屏握持（正面）",
            "裤兜",
            "手机架"
    };

    public String userPosition[] = new String[] {
            "坐",
            "站",
            "走"
    };

    public String negativeTask[] = new String[] {
            "打字",
            "浏览",
            "拍照",
            "裤兜（坐）",
            "裤兜（走）",
            "握持（走）",
            "桌上",
            "接听",
    };

    public String getTaskDescription() {
        String s = String.valueOf(task_id + 1) + " / " + String.valueOf(tasks.size()) +
                ": " + String.valueOf(repeat_times + 1) + "\n";
        String comp[] = tasks.get(task_id).split("\n");
        s += "姿态: " + comp[0] + "\n";
        s += "起始位置: " + comp[1] + "\n";
        s += "任务: " + comp[2] + "\n";
        if (repeat_times < 5)
            s += "右手\n";
        else
            s += "左手\n";
        s += commands[speechList.get(task_id * 10 + repeat_times)] + "\n";
        return s;
    }

    public void changeTaskId(int id) {
        if (id <= 0) return;
        if (id >= tasks.size())
            task_id = tasks.size() - 1;
        else
            task_id = id - 1;
        repeat_times = 0;
    }

    public String prevTask() {
        repeat_times -= 1;
        if (repeat_times < 0) {
            if (task_id > 0) {
                task_id -= 1;
                repeat_times = 9;
            } else
                repeat_times = 0;
        }
        return getTaskDescription();
    }

    public String nextTask() {
        repeat_times += 1;
        if (repeat_times >= 10) {
            repeat_times = 0;
            task_id += 1;
            if (task_id >= tasks.size())
                task_id = 0;
        }
        return getTaskDescription();
    }

    public String commands[] = new String[] {
            "1. 打开微信，给我妈发消息。",
            "2. 给我爸发微信消息。",
            "3. 打开微信，给同学发语音消息。",
            "4. 发送一条短信。",
            "5. 给爸爸发送短信。",
            "6. 发送短信给爸爸。",
            "7. 给老板打电话。",
            "8. 和奶奶视频通话。",
            "9. 查看今天的日程。",
            "10. 告诉我今天的日程。",
            "11. 明天有哪些日程？",
            "12. 最近有哪些日程安排？",
            "13. 告诉我明天的天气。",
            "14. 明天的天气怎么样？",
            "15. 明天的天气质量如何？",
            "16. 添加明天早上8点的闹钟。",
            "17. 取消今晚的所有闹钟。",
            "18. 明天早上7点叫醒我。",
            "19. 提醒我明天下午5点完成这件事。",
            "20. 提醒我明天早上给老板汇报结果。",
            "21. 查看最近的短信。",
            "22. 回复刚刚的来信。",
            "23. 查看未接来电。",
            "24. 回拨第一个号码。",
            "25. 告诉我现在的位置。",
            "26. 告诉我回家的路。",
            "27. 告诉我最近的洗手间位置。",
            "28. 附近有哪些餐馆？",
            "29. 播放我最喜爱的音乐。",
            "30. 播放下一首歌曲。",
            "31. 收藏这首歌曲。",
            "32. 收藏上一首歌曲。"

    };

    //SensorActivity
    public String triggerPosition[] = new String[] {
            "竖直对脸，碰触鼻子",
            "竖直对脸，不碰鼻子",
            "竖屏握持，上端遮嘴",
            "水平端起，倒话筒",
            "话筒",
            "横屏"
    };
}
