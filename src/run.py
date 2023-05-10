from flask import Flask, make_response, request, send_file, jsonify, Response
from flask_cors import CORS  # 解决跨域的问题
import os
from pathlib import Path
import base64

app = Flask(__name__)
cors = CORS(app)

# 导入实现算法需要用到的模块
from mycontroller import MainWindowController
from myviewmodel import VideoHandler, ViewModel
from utility import config
import argparse

import tkinter as tk
from tkinter import filedialog
from tkinter import messagebox

# 对视频进行检测的函数
def _examine_videos(dest_dir, indexes, controller) -> bool:
    # 获取上一次的保存地址
    print(dest_dir)
    config.update_last_save_dir(dest_dir)
    has_examined_video = False

    for idx in indexes:
        handler = controller.model.get(idx)
        if handler.is_examined():
            has_examined_video = True

    print('has_examined_video:', has_examined_video)
    return has_examined_video

# 检测单个视频的函数
def on_examine_one_video(dest_dir, idx, controller, type) -> bool:
    # 检测单个视频时，先判断是否已经质检过一次，是的话让用户进行选择
    if dest_dir:
        has_examined = _examine_videos(dest_dir, [idx], controller)
        if has_examined:
            return True
        else:
            try:
                print('开始进行检测\n')
                controller.examine_video(idx, dest_dir, type)
                print(controller.summary_queue)

            except:
                print('检测出错！')
                return False
            return True


dest_dir = ''
@app.route('/video/detect', methods=['post'])
async def detectOne():
    global dest_dir
    # 获取前端传递的信息
    files = request.files.getlist('files[]')  # 获取文件列表，FileStorage类型
    idx = int(request.form.get('idx'))
    type = request.form.get('type')
    audit = request.form.getlist('audit[]')
    # executor, workstation, date_time, memo = audit
    # print(idx, type, files)
    # print(executor, workstation, date_time, memo)

    if type == 'fog':
        # 如果当前视频序列为空，则将files添加进去
        if len(controller_fog.model._video_handlers) == 0:
            print('当前视频序列为空，将files添加进去')
            for f in files:
                addVideo(f, type)

        # 设置视频详细信息
        controller_fog.set_video_details(idx, audit)

        # 对单个视频文件进行检测
        on_examine_one_video(dest_dir, idx, controller_fog, type)

        res = open(dest_dir + '/' + Path(controller_fog.model.get(idx).video_path()).stem + '/summary.html', 'rb')
        return Response(res, mimetype='text/html')
    else:
        # 如果当前视频序列为空，则将files添加进去
        if len(controller_tv.model._video_handlers) == 0:
            print('当前视频序列为空，将files添加进去')
            for f in files:
                addVideo(f)

        # 设置视频详细信息
        controller_tv.set_video_details(idx, audit)

        # 对单个视频文件进行检测
        has_examined_video = on_examine_one_video(dest_dir, idx, controller_tv, type)

        print('是否检测完成：', has_examined_video)

        # TODO 把被动返回检测结果变成get_result用户主动拉取
        if has_examined_video:
            summary_path = dest_dir + '/' + Path(controller_tv.model.get(idx).video_path()).stem + '/summary.html'
            if os.path.exists(summary_path):
                res = open(summary_path, 'rb')
                return Response(res, mimetype='text/html')


# 将视频文件添加到viewmodel中
@app.route('/video/add', methods=['post'])
def add():
    file = request.files.getlist('files[]')[0]
    type = request.form.get('type')
    addVideo(file, type)
    print('已经将视频{}加入列表'.format(file.filename))
    return '已经将{}加入视频列表'.format(file.filename)

def addVideo(file, type):
    buffer_video = file.read()

    file_path = './temp/' + type
    if (not os.path.exists(file_path)):
        os.mkdir(file_path)  # 创建文件夹
    file_path = os.path.join(file_path, file.filename.split('/')[-1])
    print(file.filename)
    if os.path.exists(file_path):
        os.remove(file_path)
    with open(file_path, "wb+") as out_file:
        out_file.write(buffer_video)

    if type=='fog':
        controller_fog.add_video(file_path)
    elif type=='tv':
        controller_tv.add_video(file_path)


@app.route('/result', methods=['get'])
def getResults():
    res = {
        'files': [],
        'other': '这是其它信息'
    }
    # a = Response(open('./results/屏锥玻璃2号工位_29D6E130_1669338406_1/summary.html', 'rb').read(), mimetype='text/html')

    res['files'].append('a')
    res['files'].append('b')
    return jsonify(res)
    # return send_file('./results/屏锥玻璃2号工位_29D6E130_1669338406_1/summary.html', mimetype='text/html')
    # return make_response()

parser = argparse.ArgumentParser()
parser.add_argument('--use-detectors', action='store_true')
parser.add_argument('--kill-all-when-exit', action='store_true')
if __name__ == '__main__':
    args = parser.parse_args()

    # 创建controller控制类
    controller_fog = MainWindowController(args.use_detectors)
    viewmodel_fog = ViewModel()
    controller_fog.set_model(viewmodel_fog)

    controller_tv = MainWindowController(args.use_detectors)
    viewmodel_tv = ViewModel()
    controller_tv.set_model(viewmodel_tv)

    # 预先设置保存地址
    # if dest_dir == '':
    #     # 实例化tkinter
    #     root = tk.Tk()
    #     root.withdraw()
    #     messagebox.showinfo("提示", "请先选择检测结果保存的文件夹")
    #     dest_dir = filedialog.askdirectory()  # 选择文件夹
    #     print('\n检测结果保存地址：', dest_dir)
    dest_dir = 'D:/screenproject/TVR/src/results'
    app.run(host='127.0.0.1', port=5000)

    # controller.exit(kill_all=args.kill_all_when_exit)
    # config.save_config()
