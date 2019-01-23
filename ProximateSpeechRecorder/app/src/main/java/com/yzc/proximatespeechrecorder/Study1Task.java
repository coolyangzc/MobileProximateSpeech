package com.yzc.proximatespeechrecorder;

import java.util.ArrayList;
import java.util.Collections;
import java.util.List;

public class Study1Task {

    public int task_id, repeat_times;
    public List<String> positiveTasks, tasks;

    Study1Task() {
        positiveTasks = new ArrayList<>();
        for (String s: startPosition)
            for (String t: triggerPosition)
                for (String u: userPosition)
                    positiveTasks.add(s + "->" + t + " " + u);
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
            "裤兜（正面）",
            "裤兜（反面）",
            "手机架"
    };

    public String triggerPosition[] = new String[] {
            "竖直对脸，碰触鼻子",
            "竖直对脸，不碰鼻子",
            "平端，倒话筒",
            "话筒",
            "横屏"
    };

    public String userPosition[] = new String[] {
            "坐",
            "站",
            "走"
    };

    public String command[] = new String[] {
            "打开微信"
    };

    public String negativeTask[] = new String[] {
            "打字",
            "浏览",
            "拍照",
            "裤兜",
            "桌上",
            "接听",
    };

    public String getCurrentTask() {
        return tasks.get(task_id);
    }

    public String nextTask() {
        repeat_times += 1;
        if (repeat_times >= 3) {
            repeat_times = 0;
            task_id += 1;
            if (task_id >= tasks.size())
                task_id = 0;
        }
        return tasks.get(task_id);
    };
}
