package com.yzc.proximatespeechrecorder;

import java.util.ArrayList;
import java.util.Collections;
import java.util.List;

public class Study1Task {

    public int task_id, repeat_times;
    public List<String> positiveTasks, tasks;

    Study1Task() {
        positiveTasks = new ArrayList<>();
        for (String u: userPosition)
            for (String s: startPosition)
                for (String t: triggerPosition)
                    positiveTasks.add(u + " " + s + " " + t);
        tasks = positiveTasks;
        Collections.addAll(tasks, negativeTask);
        task_id = repeat_times = 0;
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

    public String triggerPosition[] = new String[] {
            "竖直对脸，碰触鼻子",
            "竖直对脸，不碰鼻子",
            "竖屏握持，上端遮嘴",
            "水平端起，倒话筒",
            "话筒",
            "横屏"
    };

    public String userPosition[] = new String[] {
            "坐",
            "站",
            "走"
    };

    /*public String command[] = new String[] {
            "打开微信",
            "静音",
            "截屏",
            "接听",
            "我们9点见面"
    };*/

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
        String comp[] = tasks.get(task_id).split(" ");
        for (String c: comp)
            s += c + "\n";
        return s;
    }

    public void changeTaskId(int id) {
        if (id <= 0) return;
        task_id = id - 1;
        repeat_times = 0;
    }

    public String nextTask() {
        repeat_times += 1;
        if (repeat_times >= 3) {
            repeat_times = 0;
            task_id += 1;
            if (task_id >= tasks.size())
                task_id = 0;
        }
        return getTaskDescription();
    };
}
