from datetime import datetime
import os
import re
import subprocess
import time
from PIL import Image, ImageFilter
import cv_util, ocr_util
import cv2
import numpy as np

base_dir = os.path.dirname(__file__)

jietu = "pic/screenshot.png"


def select_device():
    """选择需要连接的设备"""
    string = subprocess.Popen("adb devices", shell=True, stdout=subprocess.PIPE)
    totalstring = string.stdout.read()
    totalstring = totalstring.decode("utf-8")
    # print(totalstring)
    devicelist = re.compile(r"([A-Za-z0-9.:]*)\s*device\b").findall(totalstring)
    devicenum = len(devicelist)
    if devicenum == 0:
        print("当前无设备连接电脑,请检查设备连接情况!")
        return False
    elif devicenum == 1:
        print("当前有一台设备连接，编号:%s." % devicelist[0])
        return devicelist[0]
    else:
        print("当前存在多台设备连接! 输入数字选择对应设备:")
        dictdevice = {}
        for i in range(devicenum):
            string = subprocess.Popen(
                "adb -s %s shell getprop ro.product.device" % devicelist[i],
                shell=True,
                stdout=subprocess.PIPE,
            )
            modestring = string.stdout.read().strip()  # 去除掉自动生成的回车
            print("%s:%s---%s" % (i + 1, devicelist[i], modestring))
            dictdevice[i + 1] = devicelist[i]
        num = input()
        num = int(num)
        while not num in dictdevice.keys():
            print("输入不正确，请重新输入：")
            num = input()
            num = int(num)
        return dictdevice[num]


class Fudai:

    def __init__(self):
        self.device_id = select_device()
        self.needswitch = False
        self.switch_direction_flag = True
        pass

    def get_screenshot(self, tip=''):
        """截图3个adb命令需要2S左右的时间"""
        path = base_dir + "/pic"
        if not os.path.exists(path):
            os.makedirs(path)
        try:
            subprocess.Popen(
                "adb -s %s shell screencap -p /sdcard/DCIM/screenshot.png"
                % self.device_id,
                shell=True,
            ).wait()  # -p: save the file as a png
            subprocess.Popen(
                "adb -s %s pull /sdcard/DCIM/screenshot.png %s "
                % (self.device_id, path),
                stdout=subprocess.PIPE,
                shell=True,
            ).wait()
            timetag = datetime.now().strftime("%H:%M:%S")
            print("{}【{}】屏幕截图".format(timetag, tip))
            return True
        # subprocess.Popen('adb  -s %s shell rm /sdcard/DCIM/screenshot.png' % self.device_id, shell=True).wait()
        except:
            subprocess.Popen(
                "adb -s %s shell screencap -p /sdcard/DCIM/screenshot1.png"
                % self.device_id,
                shell=True,
            ).wait()
            subprocess.Popen(
                "adb -s %s shell mv /sdcard/DCIM/screenshot1.png /sdcard/DCIM/screenshot.png"
                % self.device_id,
                shell=True,
            ).wait()
            self.get_screenshot()

    def open_zhibo(self):
        # adb shell reboot
        # adb shell input keyevent KEYCODE_WAKEUP
        # adb shell input swipe 300 1000 300 500
        # adb shell am start -n com.ss.android.ugc.aweme.lite/com.ss.android.ugc.aweme.splash.SplashActivity
        try:
            # 解锁，并尝试打开抖音
            print("step1: 解锁，并尝试打开抖音")
            os.system(
                "adb -s %s shell input keyevent KEYCODE_WAKEUP"
                % self.device_id
                ) # -p: save the file as a png
            os.system(
                "adb -s %s shell input swipe 300 1000 300 500"
                % self.device_id
                )
            os.system(
                "adb -s %s shell am start -n com.ss.android.ugc.aweme.lite/com.ss.android.ugc.aweme.splash.SplashActivity"
                % self.device_id
            )

            time.sleep(30)


            self.get_screenshot('首页')
            result = ocr_util.ocr_img(jietu)
            print("step2: 准备点击首页'关注'按钮"+str(result))
            for idx in range(len(result)):
                item = result[idx]
                text = item[1][0]
                if text == "关注":
                    xy = cv2.minAreaRect(np.float32(item[0]))
                    print("     找到'关注'按钮，开始点击"+str(xy))
                    os.system(
                        "adb -s {} shell input tap {} {}".format(
                            self.device_id, xy[0][0], xy[0][1]
                        )
                    )
                    break
            else:
                print("     未找到'关注'按钮， 点击固定位置")
                os.system(
                    "adb -s {} shell input tap 444 159".format(
                        self.device_id
                    )
                )

            self.get_screenshot('首页')
            result = ocr_util.ocr_img(jietu)
            print("step3: 获取到点击首页关注后的ocr结果："+str(result))

            for idx in range(len(result)):
                item = result[idx]
                text = item[1][0]
                if text == "粉丝团":
                    xy = cv2.minAreaRect(np.float32(item[0]))
                    print("     找到'粉丝团'按钮，开始点击"+str(xy))
                    os.system(
                        "adb -s {} shell input tap {} {}".format(
                            self.device_id, xy[0][0], xy[0][1]
                        )
                    )
                    break
            else:
                print("     未找到数丝团按钮，直接点击固定位置")
                os.system(
                    "adb -s {} shell input tap 430 368".format(
                        self.device_id
                    )
                )

            return True
        except Exception as ex:
            print(ex)

            subprocess.Popen(
                "adb -s %s shell reboot"
                % self.device_id
            ).wait()  # -p: save the file as a png

            print('尝试恢复失败， 让设备重新启动 ！！！！ 并等待 60s')

            time.sleep(60)

    def check_have_fudai(self):
        loop = 0
        while loop < 6:  # 每3秒识别一次，最多等待18秒
            time.sleep(1.5)
            self.get_screenshot('获取福袋')
            rect = cv_util.zhaotu(jietu, "pic/fudai.png")
            if rect is not None:
                return rect
            loop += 1
        return None

    def meiyouchouzhong(self):
        self.get_screenshot('没有抽中')
        result = ocr_util.ocr_img(jietu)
        not_fudai = False
        for idx in range(len(result)):
            item = result[idx]
            text = item[1][0]
            if text == "没有抽中福袋":
                not_fudai = True
        if not_fudai:
            for idx in range(len(result)):
                item = result[idx]
                text = item[1][0]
                if text == "我知道了":
                    min_rect = cv2.minAreaRect(np.float32(item[0]))
                    return min_rect[0]
        return None

    def jiaruchoujiang(self):
        self.get_screenshot('加入抽奖')
        result = ocr_util.ocr_img(jietu)
        for idx in range(len(result)):
            item = result[idx]
            text = item[1][0]
            if text == "一键发表评论":
                min_rect = cv2.minAreaRect(np.float32(item[0]))
                return (1, min_rect[0])
            elif text == "加入粉丝团":
                min_rect = cv2.minAreaRect(np.float32(item[0]))
                return (0, min_rect[0])
            elif text == '参与成功等待开奖':
                min_rect = cv2.minAreaRect(np.float32(item[0]))
                return (2, min_rect[0])
            elif text == '活动已结束':
                min_rect = cv2.minAreaRect(np.float32(item[0]))
                return (3, min_rect[0])
        return None

    def zhibojieshu(self):
        self.get_screenshot('直播结束')
        result = ocr_util.ocr_img(jietu)
        for idx in range(len(result)):
            item = result[idx]
            text = item[1][0]
            if text == "直播已结束":
                min_rect = cv2.minAreaRect(np.float32(item[0]))
                return min_rect[0]
        return None

    def qiehuanzhibojian(self):
        if self.switch_direction_flag:
            os.system(
                "adb -s %s shell input swipe 760 1600 760 800 200"
                % (self.device_id)
            )
        else:
            os.system(
                "adb -s %s shell input swipe 760 800 760 1600 200"
                % (self.device_id)
            )
        print("切换直播间")

    def choujiang(self):
        """默认不切换直播间"""
        zhongjiang_count = 0
        while True:
            rect = self.check_have_fudai()
            shijian = ""
            shijian_seconds = -1
            while True:
                if rect:
                    os.system(
                        "adb -s {} shell input tap {} {}".format(
                            self.device_id, rect[0][0], rect[0][1]
                        )
                    )  # 点击默认小福袋的位置
                    print("点击打开福袋详情")
                    time.sleep(5)

                    wh = rect[1]
                    w = int(wh[0])
                    h = int(wh[1])

                    xy = rect[0]
                    x = int(xy[0]) - int(w // 2)
                    y = int(xy[1]) - int(h // 2)

                    jietu_image = cv2.imread(jietu)
                    crop_img = jietu_image[y : y + h, x : x + w]
                    crop_img_path = "pic/fudai_crop.png"
                    cv2.imwrite(crop_img_path, crop_img)

                    ocr_result = ocr_util.ocr_img(crop_img_path)
                    if ocr_result:
                        shijian = ocr_result[0][1][0]
                        shijian_seconds = int(shijian[0:2]) * 60 + int(shijian[3:])

                xy = self.jiaruchoujiang()
                if xy:
                    if xy[0] == 1:
                        os.system(
                            "adb -s {} shell input tap {} {}".format(
                                self.device_id, xy[1][0], xy[1][1]
                            )
                        )
                        print("点击一键发表评论")
                        time.sleep(5)
                        break
                    elif xy[0] == 0:
                        os.system(
                            "adb -s {} shell input keyevent 4".format(self.device_id)
                        )
                        self.switch_direction_flag = not self.switch_direction_flag
                        time.sleep(1)
                        self.qiehuanzhibojian()
                        print("加入粉丝团? => 后退 => 切换直播间")
                    elif xy[0] == 2:
                        os.system(
                            "adb -s {} shell input keyevent 4".format(self.device_id)
                        )
                        print("参与成功等待开奖 => 后退")
                        break
                    elif xy[0] == 3:
                        os.system(
                            "adb -s {} shell input keyevent 4".format(self.device_id)
                        )
                        print("活动已结束 => 后退")
                        break
                else:
                    break

            if shijian_seconds != -1:
                if shijian_seconds > 900:
                    shijian_seconds = 900
                print("等待：" + shijian + " : " + str(shijian_seconds))
                time.sleep(shijian_seconds)

            xy = self.meiyouchouzhong()
            if xy:
                os.system(
                    "adb -s {} shell input tap {} {}".format(
                        self.device_id, xy[0], xy[1]
                    )
                )
                print("没有抽中福袋, 点击我知道了")
                time.sleep(5)

            xy = self.zhibojieshu()
            if xy:
                self.qiehuanzhibojian()
                time.sleep(5)
                pass

            zhongjiang_count += 1

            if zhongjiang_count > 12:
                self.qiehuanzhibojian()
                time.sleep(5)
                zhongjiang_count = 0
                pass


def main():
    fudai = Fudai()
    # fudai.open_zhibo()
    fudai.choujiang()


if __name__ == "__main__":
    while True:
        try:
            main()
        except cv2.error as opencv_ex:
            print(f"捕获到其他 OpenCV 异常：{opencv_ex}")
            # 检查异常信息是否包含特定的错误信息
            error_message = str(opencv_ex)
            if "_queryDescriptors.type() == trainDescType" in error_message:
                print("手机可能发生过重启，当前处于锁屏状态，尝试恢复！！！")
                Fudai().open_zhibo()
        except Exception as ex:
            print(ex)

# adb shell reboot
# adb shell input keyevent KEYCODE_WAKEUP
# adb shell input swipe 300 1000 300 500
# adb shell am start -n com.ss.android.ugc.aweme.lite/com.ss.android.ugc.aweme.splash.SplashActivity