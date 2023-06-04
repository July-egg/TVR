from flask import Flask, make_response, request, send_file, jsonify, Response
from flask_cors import CORS  # 解决跨域的问题
import os
from pathlib import Path
import time
import json
import base64

app = Flask(__name__)
cors = CORS(app)

# 导入实现算法需要用到的模块
from controller_backend import MainWindowController
from viewmodel_backend import VideoHandler, ViewModel
from utility import config
import argparse

dest_dir = ''


def _examine_videos(dest_dir, indexes, controller) -> bool:
    # 获取上一次的保存地址
    print(dest_dir)
    config.update_last_save_dir(dest_dir)
    has_examined_video = False

    for idx in indexes:
        handler = controller.viewmodel.get(idx)
        if handler.is_examined():
            has_examined_video = True

    print('has_examined_video:', has_examined_video)
    return has_examined_video


def on_examine_one_video(dest_dir, idx, controller, video_type) -> bool:
    # 检测单个视频时，先判断是否已经质检过一次，是的话让用户进行选择
    if dest_dir:
        has_examined = _examine_videos(dest_dir, [idx], controller)
        if has_examined:
            return True
        else:
            try:
                print('开始进行检测\n')
                controller.examine_video(idx, dest_dir, video_type)
                # print(controller.summary_queue)
            except:
                print('检测出错！')
                return False
            return True


@app.route('/video/detect', methods=['post'])
async def detectOne():
    global dest_dir
    # 获取前端传递的信息
    files = request.files.getlist('files[]')  # 获取文件列表，FileStorage类型
    idx = int(request.form.get('idx'))
    video_type = request.form.get('type')
    audit = request.form.getlist('audit[]')
    # executor, workstation, date_time, memo = audit
    # print(idx, type, files)
    # print(executor, workstation, date_time, memo)

    if video_type == 'fog':
        # 如果当前视频序列为空，则将files添加进去
        if len(controller.viewmodel._video_handlers) == 0:
            print('当前视频序列为空，将files添加进去')
            for f in files:
                addVideo(f, video_type)

        # 设置视频详细信息
        controller.set_video_details(idx, audit)

        # 对单个视频文件进行检测
        on_examine_one_video(dest_dir, idx, controller, video_type)

        res = open(dest_dir + '/' + Path(controller.viewmodel.get(idx).video_path()).stem + '/summary.html', 'rb')
        return Response(res, mimetype='text/html')
    else:
        # 如果当前视频序列为空，则将files添加进去
        if len(controller.viewmodel._video_handlers) == 0:
            print('当前视频序列为空，将files添加进去')
            for f in files:
                addVideo(f, video_type)

        # 设置视频详细信息
        controller.set_video_details(idx, audit)

        # 对单个视频文件进行检测
        # has_examined_video = on_examine_one_video(dest_dir, idx, controller, video_type)
        has_examined_video = True

        print('是否检测完成：', has_examined_video)

        # TODO 把被动返回检测结果变成get_result用户主动拉取
        if has_examined_video:
            summary_path = dest_dir + '/' + Path(controller.viewmodel.get(idx).video_path()).stem + '/summary.html'
            print(summary_path)
            wait_time = 10
            while wait_time > 0:
                if os.path.isfile(summary_path):
                    res = open(summary_path, 'rb')
                    return Response('success')
                    # return Response(res, mimetype='text/html')
                else:
                    wait_time -= 1
                    print('未检测到结果文件,继续检测%d次'.format(wait_time))
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

    file_path = './temp/' + video_type
    if not os.path.exists(file_path):
        os.mkdir(file_path)  # 创建文件夹
    file_path = os.path.join(file_path, file.filename.split('/')[-1])
    print(file.filename)
    if os.path.exists(file_path):
        os.remove(file_path)
    with open(file_path, "wb+") as out_file:
        out_file.write(buffer_video)

    controller.add_video(file_path)


# TODO：根据idx删除视频列表中的文件,需要在controller和viewmodel类中写对应的函数
@app.route('/video/delete', methods=['post'])
def deleteVideo():
    params = request.get_json(silent=True)
    i, type = params['idx'], params['type']

    # TODO：调用controller类

    return '删除{}视频文件{}'.format(i, type)


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
        'PhosphorWhite': '荧光粉(白印残留)'
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
                        json_info['Proceduces'][i]['AbsoluteStartTime'] + '-' + json_info['Proceduces'][0][
                            'AbsoluteEndTime'],
                        json_info['Proceduces'][i]['RelativeStartTime'],
                        json_info['Proceduces'][i]['KeyFrameTime'],
                        res_map[json_info['Proceduces'][i]['ExaminationResult']],
                    ] for i in range(json_info['Summary']['Total'])
                ]
            }

            return Response(json.dumps(data), mimetype='application/json')
        else:
            wait_time -= 1
            print('未检测到json文件,继续检测%d次'.format(wait_time))
            time.sleep(10)
    return Response('error')


@app.route('/result/image', methods=['post'])
def getImage():
    data = request.get_json(silent=True)
    name = data['name']
    idx = data['idx']
    img_path = dest_dir + '/' + name + '/images/00' + str(idx) + '.jpg'
    print('img文件路径:' + img_path)
    # imgs = [f for f in os.listdir(img_path) if os.path.isfile(f)]

    wait_time = 10
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
            print('未检测到image文件,继续检测%d次'.format(wait_time))
            time.sleep(10)

    return Response('error')


@app.route('/result/excel', methods=['post'])
def getExcel():
    data = request.get_json(silent=True)
    name = data['name']
    excel_path = dest_dir + '/' + name + '/__src/' + name + '.xls'
    print('excel文件路径:' + excel_path)

    wait_time = 10
    while wait_time > 0:
        if os.path.isfile(excel_path):
            return send_file(excel_path, mimetype="application/vnd.ms-excel")
        else:
            wait_time -= 1
            print('未检测到excel文件,继续检测%d次'.format(wait_time))
            time.sleep(10)
    return Response('error')


parser = argparse.ArgumentParser()
parser.add_argument('--use-detectors', action='store_true')
parser.add_argument('--kill-all-when-exit', action='store_true')
if __name__ == '__main__':
    args = parser.parse_args()

    # 创建controller控制类
    controller = MainWindowController(args.use_detectors)
    viewmodel = ViewModel()
    controller.set_viewmodel(viewmodel)

    # 预先设置保存地址
    # if dest_dir == '':
    #     # 实例化tkinter
    #     root = tk.Tk()
    #     root.withdraw()
    #     messagebox.showinfo("提示", "请先选择检测结果保存的文件夹")
    #     dest_dir = filedialog.askdirectory()  # 选择文件夹
    #     print('\n检测结果保存地址：', dest_dir)
    dest_dir = './results'
    app.run(host='127.0.0.1', port=5000)

    # controller.exit(kill_all=args.kill_all_when_exit)
    # config.save_config()
