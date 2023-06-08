from flask import Flask, make_response, request, send_file, jsonify, Response
from flask_cors import CORS  # 解决跨域的问题
import os
import shutil
from pathlib import Path
import time
import json
import base64
from datetime import datetime, timedelta

app = Flask(__name__)
cors = CORS(app)

# 导入实现算法需要用到的模块
from controller_backend import MainController
from viewmodel_backend import VideoHandler, ViewModel
from utility import config
import argparse

dest_dir = ''


def _examine_videos(dest_dir, index, controller) -> bool:
    # 获取上一次的保存地址
    # print(dest_dir)
    config.update_last_save_dir(dest_dir)
    has_examined_video = False

    handler = controller.viewmodel.get(index)
    if handler.is_examined():
        has_examined_video = True

    # print('has_examined_video:', has_examined_video)
    return has_examined_video


def on_examine_one_video(dest_dir, idx, controller, video_type) -> bool:
    # 检测单个视频时，先判断是否已经质检过一次，是的话让用户进行选择
    if dest_dir:
        has_examined = _examine_videos(dest_dir, idx, controller)
        if has_examined:
            return True
        else:
            controller.examine_video(idx, dest_dir, video_type)
            while controller.get_processing():
                print("正在检测中...")
                time.sleep(10)
            return True
    return False


def _examine_all_videos(dest_dir, indexes, controller, video_type) -> bool:
    if dest_dir:
        for idx in indexes:
            has_examined = _examine_videos(dest_dir, idx, controller)
            if has_examined:
                continue
            else:
                controller.examine_video(idx, dest_dir, video_type)

        while controller.get_processing():
            print("正在检测中...")
            time.sleep(10)
        return True
    return False


@app.route('/video/detect', methods=['post'])
async def detectOne():
    global dest_dir
    # 获取前端传递的信息
    files = request.form.getlist('files[]')  # 获取文件名列表
    forward_idx = int(request.form.get('idx'))
    video_type = request.form.get('type')
    audit = request.form.getlist('audit[]')
    # executor, workstation, date_time, memo = audit
    print(forward_idx, video_type, files)
    # print(executor, workstation, date_time, memo)
    print('files', files[forward_idx])

    # 获取当前视频的序列号
    idx = forward_idx
    for i in range(len(maincontroller.viewmodel._video_handlers)):
        video_path = maincontroller.viewmodel.get(i).video_path()
        fileName = os.path.basename(video_path)
        if files[forward_idx] == fileName:
            idx = i
            print('fileName', fileName)
            print(idx)

    # 设置视频详细信息
    maincontroller.set_video_details(idx, audit)

    # 对单个视频文件进行检测
    has_examined_video = on_examine_one_video(dest_dir, idx, maincontroller, video_type)
    # has_examined_video = True

    print('是否检测完成：', has_examined_video)

    if has_examined_video:
        summary_path = os.path.join(os.path.join(dest_dir, Path(maincontroller.viewmodel.get(idx).video_path()).stem), 'summary.json')
        # print(summary_path)
        wait_time = 10
        while wait_time > 0:
            if os.path.isfile(summary_path):
                return Response('success')
            else:
                wait_time -= 1
                print('未检测到结果文件,继续检测{:d}次'.format(wait_time))
                time.sleep(10)

        return Response('error')


@app.route('/video/detectAll', methods=['post'])
async def detectMul():
    global dest_dir
    # 获取前端传递的信息
    files = request.form.getlist('files[]')  # 获取文件名列表
    video_type = request.form.get('type')
    audit = request.form.getlist('audit[]')
    # executor, workstation, date_time, memo = audit
    # print(idx, type, files)
    # print(executor, workstation, date_time, memo)

    # 获取当前视频的序列号
    indexes = []
    for i in range(len(maincontroller.viewmodel._video_handlers)):
        video_path = maincontroller.viewmodel.get(i).video_path()
        fileName = os.path.basename(video_path)
        for j in range(len(files)):
            if files[j] == fileName:
                print('fileName', fileName)
                indexes.append(i)
                maincontroller.set_video_details(i, audit)

    # 对单个视频文件进行检测
    has_examined_video = _examine_all_videos(dest_dir, indexes, maincontroller, video_type)

    print('是否检测完成：', has_examined_video)

    if has_examined_video:
        summary_path = os.path.join(os.path.join(dest_dir, Path(maincontroller.viewmodel.get(indexes[0]).video_path()).stem), 'summary.json')
        # print(summary_path)
        wait_time = 10
        while wait_time > 0:
            if os.path.isfile(summary_path):
                return Response('success')
            else:
                wait_time -= 1
                print('未检测到结果文件,继续检测{:d}次'.format(wait_time))
                time.sleep(10)

        return Response('error')


@app.route('/video/add', methods=['post'])
def add():
    file = request.files.getlist('files[]')[0]
    video_type = request.form.get('type')
    addVideo(file, video_type)
    print('已经将视频{}加入列表'.format(file.filename))
    return '已经将{}加入视频列表'.format(file.filename)


def addVideo(file, video_type):
    buffer_video = file.read()

    file_path = os.path.join(config.get_last_video_dir(), video_type)
    if not os.path.exists(file_path):
        os.mkdir(file_path)  # 创建文件夹
    file_path = os.path.join(file_path, file.filename.split('/')[-1])
    print(file_path)
    if os.path.exists(file_path):
        os.remove(file_path)
    with open(file_path, "wb+") as out_file:
        out_file.write(buffer_video)

    maincontroller.add_video(file_path)


# TODO：根据idx删除视频列表中的文件,需要在controller和viewmodel类中写对应的函数
@app.route('/video/delete', methods=['post'])
def deleteVideo():
    params = request.get_json(silent=True)
    i, type, name = params['idx'], params['type'], params['name']

    # TODO：调用controller类

    return '删除{}视频文件{}'.format(i, type)


# 获取操作时间点函数
def operateTime(abs, rel, key):
    abs_time = datetime.strptime(abs, '%H:%M:%S')
    h, m, s = [int(float(i)) for i in rel.split(':')]
    rel_delta = timedelta(hours=h, minutes=m, seconds=s)
    h, m, s = [int(float(i)) for i in key.split(':')]
    key_delta = timedelta(hours=h, minutes=m, seconds=s)
    op_time = (abs_time - rel_delta + key_delta).strftime("%H:%M:%S")

    # print(op_time)
    return op_time

@app.route('/result/info', methods=['post'])
def getResults():
    data = request.get_json(silent=True)
    name = data['name']
    json_path = dest_dir + '/' + name + '/summary.json'
    print('json文件路径:' + json_path)

    res_map = {
        'Pass': '干净',
        'Broken': '碎屏',
        'ConeResidue': '锥体玻璃残留',
        'PhosphorResidue': '荧光粉',
        'PhosphorWater': '荧光粉(水印残留)',
        'PhosphorWhite': '荧光粉(白印残留)',
        'Fog': '漏氟'
    }
    wait_time = 10
    while wait_time > 0:
        if os.path.isfile(json_path):
            with open(json_path, 'rb') as fp:
                json_info = json.load(fp)

            data = {
                'details': {
                    '检查人': json_info['Examiner'],
                    '视频文件': json_info['VideoPath'].split("\\")[-1],
                    '工位': json_info['WorkStation'],
                    '视频录制时间': json_info['VideoStartDateTime'],
                    '备注': json_info['Note'],
                    '文档生成时间': json_info['TimeStamp'],
                },
                'results': [
                    [
                        json_info['Proceduces'][i]['SectionIndex'],
                        json_info['Proceduces'][i]['AbsoluteStartTime'] + '-' + json_info['Proceduces'][i]['AbsoluteEndTime'],
                        operateTime(json_info['Proceduces'][i]['AbsoluteStartTime'], json_info['Proceduces'][i]['RelativeStartTime'], json_info['Proceduces'][i]['KeyFrameTime']),
                        json_info['Proceduces'][i]['KeyFrameTime'],
                        res_map[json_info['Proceduces'][i]['ExaminationResult']],
                    ] for i in range(json_info['Summary']['Total'])
                ]
            }

            return Response(json.dumps(data), mimetype='application/json')
        else:
            wait_time -= 1
            print('未检测到json文件,继续检测{:d}次'.format(wait_time))
            time.sleep(10)
    return Response('error')


@app.route('/result/image', methods=['post'])
def getImage():
    data = request.get_json(silent=True)
    name = data['name']
    idx = data['idx']
    img_path = dest_dir + '/' + name + '/images/' + f'{idx:03}.jpg'
    print('img文件路径:' + img_path)
    # imgs = [f for f in os.listdir(img_path) if os.path.isfile(f)]

    wait_time = 3
    while wait_time > 0:
        if os.path.isfile(img_path):
            # img_stream = open(img_path+img, 'rb').read()
            # img_stream = base64.b64encode(img_stream)
            # images.append(img_stream)

            img_data = open(img_path, 'rb').read()
            response = make_response(img_data)
            response.headers['Content-Type'] = 'image/jpg'
            return response
        else:
            wait_time -= 1
            print('未检测到image文件,继续检测{:d}次'.format(wait_time))
            time.sleep(2)

    return Response('error')


@app.route('/result/excel', methods=['post'])
def getExcel():
    data = request.get_json(silent=True)
    name = data['name']
    excel_path = dest_dir + '/' + name + '/__src/' + name + '.xls'
    print('excel文件路径:' + excel_path)

    wait_time = 3
    while wait_time > 0:
        if os.path.isfile(excel_path):
            return send_file(excel_path, mimetype="application/vnd.ms-excel")
        else:
            wait_time -= 1
            print('未检测到excel文件,继续检测{:d}次'.format(wait_time))
            time.sleep(2)
    return Response('error')

# TODO:实现进度条的实时检测
@app.route('/progress', methods=['post'])
def getProgress():
    i, amount = maincontroller.progress_queue.get()
    ratio = round(min(100 * i / amount, 100.0), 2)
    return jsonify({'ratio': ratio})


parser = argparse.ArgumentParser()
parser.add_argument('--use-detectors', action='store_true')
parser.add_argument('--kill-all-when-exit', action='store_true')
if __name__ == '__main__':
    args = parser.parse_args()

    # 创建controller控制类
    maincontroller = MainController(args.use_detectors)
    mainviewmodel = ViewModel()
    maincontroller.set_viewmodel(mainviewmodel)

    filepath = config.get_last_video_dir()
    tvfilepath = os.path.join(filepath, 'tv')
    fogfilepath = os.path.join(filepath, 'fog')
    if os.path.exists(tvfilepath):
        shutil.rmtree(tvfilepath)
    if os.path.exists(fogfilepath):
        shutil.rmtree(fogfilepath)
    dest_dir = config.get_last_save_dir()
    app.run(host='127.0.0.1', port=5000)

    # controller.exit(kill_all=args.kill_all_when_exit)
    # config.save_config()
