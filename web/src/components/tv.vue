<template>
    <div class="wrap">
        <div class="left">
            <div class="video">
                <!--     没有打开视频文件时，显示＋号           -->
                <input type="file" id="file" hidden @change="fileChange" accept="video/*" multiple="multiple">
                <div @click="btnChange('file')" style="width:100%; height:100%; object-fit:fill; display: flex;
                     box-shadow: 0 2px 4px rgba(0, 0, 0, .12), 0 0 6px rgba(0, 0, 0, .04);" v-if="videoEmpty">
                    <div style="display: flex; justify-content: space-around; align-content: center;margin: auto;">
                        <i class="el-icon-plus" style="font-size: 38px; line-height: 38px;"></i>
                        <span style="font-size: 40px; line-height: 40px;">&nbsp;&nbsp;打开视频文件</span>
                    </div>
                </div>

                <!--    显示当前打开的视频文件         -->
                <div class="else" style="width:100%; height:100%; object-fit:fill;" v-else>
                    <div style="line-height: 25px;height: 25px;  font-size: 18px; text-overflow: ellipsis; width: 100%;">
                        <b>当前视频文件:&nbsp;</b>{{present.name}}
                    </div>
                    <video ref="video" controls :src="url" disablePictureInPicture
                         controlslist="nodownload nofullscreen noremoteplayback noplaybackrate"></video>
                </div>
            </div>

            <div class="audit" >
                <div class="auditInfo">
                    <div class="auditKey"><span style="line-height: 100%;">审查人员: </span></div>
                    <el-autocomplete v-model="audit['person']" placeholder="请输入审查人员信息" @change="auditPersonCg"
                     :fetch-suggestions="queryAuditPerson" style="line-height: 100%; height: 100%; width: 40%;"></el-autocomplete>
                </div>
                <div class="auditInfo">
                    <div class="auditKey"><span style="line-height: 100%;">工位: </span></div>
                    <el-autocomplete v-model="audit['cub']" placeholder="请输入工位" @change="auditCubCg"
                     :fetch-suggestions="queryAuditCub" style="line-height: 100%; height: 100%; width: 40%;"></el-autocomplete>
                </div>
                <div class="auditInfo">
                    <div class="auditKey"><span style="line-height: 100%;">时间: </span></div>
                    <el-date-picker v-model="audit['time']" style="line-height: 100%; height: 100%; width: 40%;"
                      type="datetime" placeholder="选择日期时间" @change="auditTimeCg">
                    </el-date-picker>
                </div>
                <div class="auditInfo">
                    <div class="auditKey"><span style="line-height: 100%">备注: </span></div>
                    <el-autocomplete v-model="audit['note']" placeholder="请输入备注" @change="auditNoteCg"
                     :fetch-suggestions="queryAuditNote" style="line-height: 100%; height: 100%; width: 50%;"></el-autocomplete>
                </div>
            </div>
        </div>

        <div class="right">
            <div class="listTitle"
                 style="line-height: 25px; font-size: 18px; display: flex; justify-content: space-between;">
                <b>当前视频列表</b>
            </div>

            <div class='addBtn'
                 style="line-height: 25px; font-size: 18px; display: flex; justify-content: space-between;">
                <el-button type="primary" @click="btnChange('file')" style="font-size: 15px; height: 25px; width:80px;
                 border-radius: 10px; padding: 0;border: none;"><b>添加文件</b></el-button>
                <el-button type="primary" @click="btnChange('folder')" style="font-size: 15px; height: 25px; width:80px;
                 border-radius: 10px; padding: 0;border: none;"><b>添加文件夹</b></el-button>
            </div>

            <input type="file" id="folder" accept=".mp4" hidden @change="fileChange" webkitdirectory>
            <div class="files">
                <div class="each" v-for="(f,i) in files" style="height: 25px; line-height: 25px; font-size: 20px;">
                    <div :class="i == presentIdx? 'chosen': 'unchosen'" >
                        <span style="width: 10px;line-height: 25px;height: 25px;" >
                            <el-popconfirm
                          confirm-button-text='好的'
                          cancel-button-text='不用了'
                          icon="el-icon-info"
                          icon-color="red"
                          title="删除视频文件？"
                          @confirm="deleteVideo(i)">
                          <el-button slot="reference"
                                     style="width:24px; line-height: 25px;height: 25px; border: none;background-color: transparent;
                                            font-size: 18px; justify-content: center;padding: 0;"
                                     icon="el-icon-remove-outline"></el-button>
                         </el-popconfirm>
                        </span>
                        <span style="line-height: 25px; width: 235px;" v-if="i == presentIdx">{{f.name}}</span>
                        <span style="line-height: 25px; width: 235px;" v-else @click="presentChange(f, i)">{{f.name}}</span>
                    </div>
                </div>
            </div>

            <div class="detectBtn"
                style="display: flex; justify-content: space-around; margin-top: 10px;height: 40px;line-height: 40px;">
                <el-button type="primary" style="width: 100px; height: 40px; border-radius: 12px; border: none; font-size: 18px;
                       box-shadow: 0 2px 4px rgba(0, 0, 0, .12), 0 0 6px rgba(0, 0, 0, .04);text-align: center; padding: 0;"
                        @click="detectOne">
                    单个检测
                  </el-button>
                <el-button type="primary" style="width: 100px; height: 40px; border-radius: 12px; border: none; font-size: 18px;
                       box-shadow: 0 2px 4px rgba(0, 0, 0, .12), 0 0 6px rgba(0, 0, 0, .04);text-align: center; padding: 0;"
                        @click="detectMul">
                    全部检测
                </el-button>

            </div>

            <div class="progress" style="height: 50px; margin-top: 15px; line-height: 50px;">
                <div style="line-height: 20px; font-size: 16px; ">当前检测进度({{num}}/{{total}})</div>
                <el-progress :percentage="ratio" style="line-height: 30px; font-size: 20px;"></el-progress>
            </div>
        </div>
    </div>
</template>

<script>
    export default {
        name: "tv",
        data(){
            return{
                // 审计人员信息
                audit:{
                    'person':'', 'cub':'', 'time':'', 'note':''
                },
                dest_dir:'',// 保存文件夹
                ratio:0,// 检测进度条
            }
        },
        methods:{
            async detectOne(){
                if(this.$store.state.tvDetecting || this.$store.state.fogDetecting){
                    this.$message({
                      showClose: true,
                      message: '有视频正在检测中！',
                      type: 'error',
                      center: true
                    });
                    return
                }

                // 首先判断是否打开了视频
                if(this.presentIdx == -1){
                    this.$message({
                      showClose: true,
                      message: '请先选择视频文件！',
                      type: 'error',
                      center: true
                    });
                    return
                }

                // 检查审查人员信息是否完善
                if(this.audit['person'] == '' || this.audit['cub']=='' || this.audit['time']=='' || this.audit['time']==null){
                    this.$message({
                      showClose: true,
                      message: '请完善质检人员信息！',
                      type: 'error',
                      center: true
                    });
                    return
                }

                console.log('进行单个视频检测')
                this.$store.commit('totalChange', [1, this.detectType])
                this.$store.commit('numChange', [1, this.detectType])

                // 将数据传入后端，参数如下：
                // type：使用的算法类型，fog(空调漏氟)，tv(电视机回收)
                // files[]：视频文件列表
                // idx：当前视频文件的索引
                // audit：审计人员信息
                // dest_dir: 保存地址
                let formdata = new FormData();
                formdata.append('type', this.detectType)
                formdata.append('idx', this.presentIdx)

                for (var key in this.audit){
                    formdata.append('audit[]', this.audit[key])
                }

                const files = this.files
                for(var k in this.files){
                    formdata.append('files[]', files[k].name)
                }

                const config = {headers: {'Content-Type': 'multipart/form-data'}}

                var name = this.files[this.presentIdx]['name'].split('.mp4')[0]

                this.$store.commit('detectState', this.detectType)

                await this.axios.post('/video/detect', formdata, config)
                .then((response) => {
                    console.log(response)
                    if(response.data == 'error'){
                        console.error('视频' + name +'检测失败')
                        this.$message({
                          showClose: true,
                          message: '视频' + name +'检测失败！',
                          type: 'error',
                          center: true
                        });
                    }else{
                        this.$message({
                          message: '视频' + name +'检测完成!',
                          type: 'info',
                          center: true
                        });
                        this.$store.dispatch('addResultA', name)
                        this.ratio = 100
                    }
                    // const blob = new Blob([response.data], {'type': 'text/html'})
                    // const blobUrl = window.URL.createObjectURL(blob)
                })
                .catch((error) => {
                    console.log(error)
                })

                this.$store.commit('detectState', this.detectType)
                this.$store.commit('totalChange', [0, this.detectType])
                this.$store.commit('numChange', [0, this.detectType])
                this.ratio = 0
            },
            async detectMul(){
                if(this.$store.state.tvDetecting || this.$store.state.fogDetecting){
                    this.$message({
                      showClose: true,
                      message: "有视频正在检测中！",
                      type: 'error',
                      center: true
                    });
                    return
                }

                // 首先判断是否打开了视频
                if(this.presentIdx == -1){
                    this.$message({
                      showClose: true,
                      message: '请先选择视频文件！',
                      type: 'error',
                      center: true
                    });
                    return
                }

                // 检查审查人员信息是否完善
                if(this.audit['person'] == '' || this.audit['cub']=='' || this.audit['time']=='' || this.audit['time']==null){
                    this.$message({
                      showClose: true,
                      message: '请完善质检人员信息！',
                      type: 'error',
                      center: true
                    });
                    return
                }

                console.log('进行全部视频检测')
                this.$store.commit('totalChange', [this.$store.state.tvList.length, this.detectType])
                this.$store.commit('numChange', [0, this.detectType])

                const config = {headers: {'Content-Type': 'multipart/form-data'}}

                const files = this.files
                // 变量当前视频文件列表，依次进行检测并获取检测结果html
                for(let i = 0; i < files.length; i++){
                    this.$store.commit('numChange', [this.num + 1, this.detectType])

                    let formdata = new FormData();
                    formdata.append('type', this.detectType)
                    formdata.append('idx', i)
                    for (var key in this.audit){
                        formdata.append('audit[]', this.audit[key])
                    }

                    for(var k in this.files){
                        formdata.append('files[]', files[k].name)
                    }

                    var name = files[i]['name'].split('.mp4')[0]

                    this.$store.commit('detectState', this.detectType)

                    await this.axios.post('/video/detect', formdata, config)
                    .then((response) => {
                        if(response.data == 'error'){
                            console.error('视频' + name +'检测失败')
                            this.$message({
                              showClose: true,
                              message: '视频' + name +'检测失败',
                              type: 'error',
                              center: true
                            });
                        }else{
                            this.$store.dispatch('addResultA', name)
                            this.$message({
                              message: '视频' + name +'检测完成!',
                              type: 'info',
                              center: true
                            });
                            this.ratio = 100
                        }
                    }).catch((error) => {
                        console.log(error)
                    })

                    this.$store.commit('detectState', this.detectType)
                    this.ratio = 0
                }

                this.$store.commit('totalChange', [0, this.detectType])
                this.$store.commit('numChange', [0, this.detectType])
            },

            // 打开视频文件与文件夹实现函数
            async fileChange(e) {
              try {
                const fu = document.getElementById(this.id)
                if (fu == null) return

                var files = fu.files
                // console.log('files：')

                for(let i = 0; i < files.length; i++){
                    let url = window.webkitURL.createObjectURL(files[i]) ;
                    files[i]['url'] = url;
                    let unrepeated = true
                    await this.$store.dispatch('fileChangeA', [files[i], this.$store.state.videoType]).then(res=>{
                        // console.log('该文件不在列表中？', unrepeated)
                        unrepeated = res
                    })

                    // 将不重复的文件发送到后端进行上传
                    if(unrepeated){
                        let formdata = new FormData();
                        // console.log(files[i]);
                        formdata.append('files[]', files[i]);
                        formdata.append('type', this.$store.state.videoType);
                        await this.axios.post('/video/add', formdata,{headers: {'Content-Type': 'multipart/form-data'}})
                        .then((response) => {
                            console.log(response.data)
                        })
                        .catch((error) => {
                            console.log(error)
                        })
                    }
                }
              }
              catch (error) {
                console.debug('choice file err:', error)
              }
            },
            btnChange(id) {
                // 打开文件夹页面进行选择
                this.id = id
                var file = document.getElementById(id)
                file.click()
            },

            presentChange(f, i){
                console.log('当前视频文件发生切换, i:', i)
                this.$store.commit('presentVideoChange', [f, i, this.$store.state.videoType])
            },
            deleteVideo(i){
                console.log('删除视频文件', this.files[i].name)
                // TODO:根据给定的i与type删除指定的视频文件
                this.axios({
                    method:'post',
                    url:'/video/delete',
                    data:{'idx':i, 'type':this.$store.state.videoType, 'name':this.$store.state.tvList[i].name}
                }).then(res=>{
                    console.log(res)
                }).catch(err=>{
                    console.log(err)
                })
                this.$store.commit('deleteVideo', [i, this.$store.state.videoType])
            },

            // 以下是审计人员信息处理函数
            auditPersonCg(){
                // console.log('审计人员改变')
                this.$store.commit('auditChange', ['person', this.audit['person']])
            },
            auditCubCg(){
                // console.log('审计人员改变')
                this.$store.commit('auditChange', ['cub', this.audit['cub']])
            },
            auditTimeCg(){
                console.log('审计人员time改变'+ this.audit['time'])
                this.$store.commit('auditChange', ['time', this.audit['time']])
            },
            auditNoteCg(){
                // console.log('审计人员改变')
                this.$store.commit('auditChange', ['note', this.audit['note']])
            },
            queryAuditPerson(queryString, callback){
                var res = [{"value":this.$store.state.audit['person']}]
                callback(res)
            },
            queryAuditCub(queryString, callback){
                var res = [{"value":this.$store.state.audit['cub']}]
                callback(res)
            },
            queryAuditNote(queryString, callback){
                var res = [{"value":this.$store.state.audit['note']}]
                callback(res)
            },

            getProgress(){
                let self = this
                if(this.detecting && this.ratio <= 100){
                    self.axios({
                        method:'post',
                        url:'/progress',
                    }).then(res=>{
                        this.ratio = res.data['ratio']
                        setTimeout(()=>{
                          self.getProgress()
                        }, 500)
                    }).catch(err=>{
                        console.log(err)
                    })
                }
            },
        },
        computed:{
            present(){ // 当前视频文件
                return this.$store.state.presentTv
            },
            presentIdx(){ // 当前视频文件的索引号
                return this.$store.state.presentTvIdx
            },
            detectType(){ // 当前是电视机还是漏氟检测
                return this.$store.state.videoType
            },
            files:{
                // 返回当前电视机视频列表
                get(){
                    return this.$store.state.tvList
                },
            },
            videoEmpty(){
                return this.$store.state.presentTv == null
            },
            url() {
                // if(this.$store.state.presentTv){
                //     return window.webkitURL.createObjectURL(this.$store.state.presentTv)
                //     return window.webkitURL.createObjectURL([this.$store.state.presentTv], {type:'video/mpeg'})
                // }else{
                //     return ''
                // }
                return this.present['url']
            },
            timeNow(){
                const t = new Date();
                return new Date(t.getFullYear(), t.getMonth(), t.getDate(), t.getHours(), t.getMinutes(), t.getSeconds())
            },
            detecting(){
                return this.$store.state.tvDetecting
            },
            total(){
                return this.$store.state.tvTotal
            },
            num(){
                return this.$store.state.tvNum
            }
        },
        watch:{
            present(newVal, oldVal){
                // console.log('当前视频发生改变...', oldVal, newVal)
            },
            presentIdx(newVal, oldVal){
                // console.log('当前视频idx发生改变...', oldVal, newVal)
            },
            files(newVal, oldVal){
                // console.log('视频文件列表files发生了修改')
            },
            '$store.state.tvDetecting':{
                deep:true,
                handler(newVal, oldVal){
                    console.log('detecting值变为', newVal)
                    if(newVal==true){
                      this.getProgress()
                    }
                }
            }
        },
        mounted() {
            if(this.$store.state.tvDetecting){
                this.getProgress()
            }
        }
    }
</script>

<style scoped>
.wrap{
    /*box-shadow: 0 2px 4px rgba(0, 0, 0, .12), 0 0 6px rgba(0, 0, 0, .04);*/
    display: flex;
    justify-content: space-between;
    padding: 0;
    margin: 0;
    width: 100%;
    height: 100%;
}

@media only screen and (max-width: 1280px){
  .left{
    width: 70%;
    height: 100%;
    display: flex;
    flex-direction: column;
    justify-content: space-between;
  }

  .right{
      width: 29%;
      height: 100%;
  }
}

@media only screen and (max-width: 1920px) and (min-width: 1281px){
  .left{
    width: 80%;
    height: 100%;
  }

  .right{
    width: 19%;
    height: 100%;
  }
}

.video{
  height: 75%; width: 100%; line-height:75%;margin: 0;
}

video{
  width:100%;
  height:calc(100% - 25px);
  object-fit:fill;
  outline:none;
}

/*审计人员信息*/
.audit{
  height: 24%;
  line-height:24%;
  box-shadow: 0 2px 4px rgba(0, 0, 0, .12), 0 0 6px rgba(0, 0, 0, .04);
  display: flex;
  flex-direction: column;
  justify-content: space-evenly;
  vertical-align: middle;
}

.auditInfo{
  height:25%;
  line-height: 25%;
  padding-left: .5rem;
  display: flex;
}

.auditKey{
  width: 2.5rem;
  height: 100%;
  line-height: 100%;
  display: flex;
  align-items: center;
  font: 700 .35rem 宋体;
}

/* 审计人员信息输入框 */
::v-deep .el-autocomplete .el-input  .el-input__inner{
    min-height: 30px;
    height: 30px;
}

::v-deep .el-date-editor .el-input__inner{
    min-height: 30px;
    height: 30px;
}



/*视频列表块*/
.each .unchosen:hover{
    background-color: #cce8ff;
    opacity: 0.5;
    width: 100%;
}

.chosen{
    /*height: 35px;*/
    /*line-height: 35px;*/
    /*font-size: 20px;*/
    height: 27px;
    line-height: 27px;
    font-size: 15px;

    white-space: nowrap;
    background-color:#cce8ff;
    border-bottom: solid;
    border-width: 1px;
    border-color: #99d1ff;
    margin: 1px 0;
}

.unchosen{
    height: 27px;
    line-height: 27px;
    font-size: 15px;
    white-space: nowrap;
    border-bottom: solid;
    border-width: 1px;
    margin: 1px 0;
    border-color: white;
}

.files{
  margin-top: 5px;
  height: calc(75% - 55px);
  overflow-y: scroll;
  overflow-x: hidden;
  box-shadow: 0 2px 4px rgba(0, 0, 0, .12), 0 0 6px rgba(0, 0, 0, .04);
}

/* 控制视频video组件的显示样式 */
video::-webkit-media-controls-fullscreen-button {
    display: none;
}
video::-webkit-media-controls-mute-button {
    display: none;
}
video::-webkit-media-controls-toggle-closed-captions-button {
    display: none;
}
video::-webkit-media-controls-volume-slider {
    display: none;
}

/*//所有控件*/
video::-webkit-media-controls-enclosure{
    opacity: 25%;
}
/*//播放按钮*/
video::-webkit-media-controls-play-button {
    /*display: none;*/
    opacity: 100%;
}
/*//进度条*/
video::-webkit-media-controls-timeline {
    /*display: none;*/
     opacity: 100%;
}
/*//观看的当前时间*/
video::-webkit-media-controls-current-time-display{
    /*display: none;*/
    opacity: 100%;
}
/*//剩余时间*/
video::-webkit-media-controls-time-remaining-display {
    /*display: none;*/
    opacity: 100%;
}


/*进度条样式*/
::v-deep .el-progress .el-progress-bar{
  height: 20px;
  line-height: 20px;
  padding: 0;
}

::v-deep .el-progress .el-progress-bar .el-progress-bar__outer{
  width: 185px;
  height: 20px;
  line-height: 20px;
  min-height: 20px;
  padding: 0;
}

::v-deep .el-progress .el-progress__text{
  width: 52px;
  margin: 0;
}
</style>