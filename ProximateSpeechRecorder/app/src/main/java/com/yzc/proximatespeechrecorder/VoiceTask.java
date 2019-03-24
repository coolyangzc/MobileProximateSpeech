package com.yzc.proximatespeechrecorder;

import android.util.Log;

import java.util.ArrayList;
import java.util.Arrays;
import java.util.Collections;
import java.util.List;
import java.util.Random;

public class VoiceTask {

    private int task_id, repeat_times;
    private List<String> tasks, sentences;
    private List<Integer> speechList = new ArrayList<>();
    private Random random;

    public VoiceTask(int seed) {
        random = new Random(seed);
        List<String> pos = new ArrayList<>(Arrays.asList(triggerPosition));
        pos.addAll(Arrays.asList(otherPosition));
        Collections.shuffle(pos, random);
        tasks = new ArrayList<>();
        for (String p: pos)
            for (String v: volume)
                tasks.add(p + " " + v);
        for(String task: tasks)
            Log.d("VOICE_TASKS", task);
        initSpeechList();
    }

    public String triggerPosition[] = new String[] {
            "竖直对脸，碰触鼻子",
            "竖直对脸，不碰鼻子",
            "竖屏握持，上端遮嘴",
            "水平端起，倒话筒",
            "话筒",
            "横屏"
    };

    public String otherPosition[] = new String[] {
            "手上正面", "手上反面",
            "桌上正面", "桌上反面",
            "耳旁打电话",
            "裤兜"
    };

    public String volume[] = new String[] {
            "大声",
            "小声"
    };

    private void initSpeechList() {
        sentences = new ArrayList<>(Arrays.asList(simpleCommands));
        sentences.addAll(Arrays.asList(commands));
        sentences.addAll(Arrays.asList(naturalLanguage));
        for (int i = 0; i < tasks.size(); ++i) {
            speechList.add(random.nextInt(simpleCommands.length));
            speechList.add(random.nextInt(commands.length) + simpleCommands.length);
            speechList.add(random.nextInt(naturalLanguage.length) +
                    simpleCommands.length + commands.length);
        }
    }

    public String getTaskDescription() {
        String s = String.valueOf(task_id + 1) + " / " + String.valueOf(tasks.size()) +
                ": " + String.valueOf(repeat_times + 1) + "\n";
        String comp[] = tasks.get(task_id).split(" ");
        for (String c: comp)
            s += c + "\n";
        return s;
    }

    public String getSpeechSentence() {
        return sentences.get(speechList.get(task_id * 3 + repeat_times));
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
                repeat_times = 2;
            } else
                repeat_times = 0;
        }
        return getTaskDescription();
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
    }


    public String simpleCommands[] = new String[] {
            "1. 打开微信    打开浏览器    打开相机    打开音乐    打开支付宝",
            "2. 打开淘宝    打开邮箱    打开微博    打开闹钟    打开记事本",
            "3. 扫码    二维码    朋友圈    搜索    添加    发送    发状态",
            "4. 截屏    静音    手电筒    最近应用    蓝牙    返回    桌面",
            "5. 复制    剪切    粘贴    撤销    重做    加粗    高亮    向左    向右"
    };
    public String commands[] = new String[] {
            "6.	打开微信，给我妈发消息。给我爸发微信消息。打开微信，给同学发语音消息。",
            "7.	发送一条短信。给爸爸发送短信。 发送短信给爸爸。给老板打电话。 和奶奶视频通话。",
            "8.	查看今天的日程。告诉我今天的日程。明天有哪些日程？ 最近有哪些日程安排？",
            "9.	告诉我明天的天气。 明天的天气怎么样？ 明天的天气质量如何？",
            "10. 添加明天早上8点的闹钟。 取消今晚的所有闹钟。 明天早上7点叫醒我。",
            "11. 提醒我明天下午5点完成这件事。 提醒我明天早上给老板汇报结果。",
            "12. 查看最近的短信。回复刚刚的来信。 查看未接来电。 回拨第一个号码。",
            "13. 告诉我现在的位置。 告诉我回家的路。 告诉我最近的洗手间位置。 附近有哪些餐馆？",
            "14. 播放我最喜爱的音乐。 播放下一首歌曲。 收藏这首歌曲。 收藏上一首歌曲。"
    };

    public static String singleCommands[] = new String[] {
            "打开微信，给我妈发消息。", "给我爸发微信消息。", "打开微信，给同学发语音消息。",
            "发送一条短信。", "给爸爸发送短信。", "发送短信给爸爸。",
            "给老板打电话。", "和奶奶视频通话。", "查看今天的日程。",
            "告诉我今天的日程。", "明天有哪些日程？", "最近有哪些日程安排？",
            "告诉我明天的天气。", "明天的天气怎么样？", "明天的天气质量如何？",
            "添加明天早上8点的闹钟。", "取消今晚的所有闹钟。", "明天早上7点叫醒我。",
            "提醒我明天下午5点完成这件事。", "提醒我明天早上给老板汇报结果。",
            "查看最近的短信。", "回复刚刚的来信。", "查看未接来电。", "回拨第一个号码。",
            "告诉我现在的位置。", "告诉我回家的路。", "告诉我最近的洗手间位置。",
            "附近有哪些餐馆？", "播放我最喜爱的音乐。", "播放下一首歌曲。",
            "收藏这首歌曲。", "收藏上一首歌曲。"
    };

    public String naturalLanguage[] = new String[] {
            "15. 小奥斯卡发现周围的世界太过荒诞，就暗下决心要永远做小孩子。",
            "16. 这一倡议得到了从事临床医学的二十八位中国工程院院士、中国科学院院士的签名赞同。",
            "17. 韩国的基本目标是射箭三块金牌，柔道三块金牌，羽毛球两块金牌，以及举重等十二块金牌。",
            "18. 这朋友也像谈恋爱一样，得讲缘份，有缘份是不用刻意去追求的。",
            "19. 乙肝病毒非常顽固，患病后往往长期不能痊愈，而且慢性乙型肝炎还有可能转为肝癌。",
            "20. 开会的会场估计只有二十二摄氏度，而午后室外的最高气温常达三十三摄氏度左右。",
            "21. 对全体员工加强外语培训，严格外语考试，并把外语成绩和本人的经济收入挂钩。",
            "22. 由于宇宙空间环境险恶，返回舱都做成密封式的，使宇航员与宇宙空间环境完全隔绝。",
            "23. 她要学习，又要帮奶奶持家。可翻阅她的作业本，根本看不到八十分以下的成绩。",
            "24. 他的时装设计既有融入前卫意识的先锋派作品，又有将艺术性与实用性完美结合的佳作。",
            "25. 这样的修养的演员即使正走红，也不过如过眼云烟而已，成不了真正意义上的艺术家。",
    };
}
