<template>
    <div class="wrap">
        <div class="left">
            <div class="video" style="height: 385px; width: 645px; line-height: 510px;margin: 0;">
                <!--     打开视频文件页面      -->
                <div @click="btnChange('file')" style="width:100%; height:100%; object-fit:fill; display: flex;
                     box-shadow: 0 2px 4px rgba(0, 0, 0, .12), 0 0 6px rgba(0, 0, 0, .04);" v-if="videoEmpty">
                    <input type="file" id="file" hidden @change="fileChange" accept=".mp4" multiple="multiple">
                    <div style="display: flex; justify-content: space-around; align-content: center;margin: auto;">
                        <i class="el-icon-plus" style="font-size: 38px; line-height: 38px;"></i>
                        <span style="font-size: 40px; line-height: 40px;">&nbsp;&nbsp;打开视频文件</span>
                    </div>
                </div>

                <div class="else" style="width:100%; height:100%; object-fit:fill;" v-else>
                    <div style="line-height: 30px; font-size: 18px; height: 30px; text-overflow: ellipsis; width: 100%;">
                        <b>当前视频文件:&nbsp;</b>{{present.name}}
                    </div>
                    <video controls :src="url" style="width:100%; height:357px; object-fit:fill;"></video>
                </div>
            </div>

            <div class="audit" style="height: 135px; line-height: 135px; margin-top:5px;box-shadow: 0 2px 4px rgba(0, 0, 0, .12), 0 0 6px rgba(0, 0, 0, .04);">
                <div style="height: 30px;line-height: 30px; margin: 3px 15px; display: flex; padding-top: 3px">
                    <div style="width: 100px; line-height: 28px; "><b>审查人员: </b></div>
                    <el-autocomplete v-model="audit['person']" placeholder="请输入审查人员信息" @change="auditPersonCg"
                     :fetch-suggestions="queryAuditPerson" style="line-height: 30px; height: 30px; width: 260px;"></el-autocomplete>
                </div>
                <div style="height: 30px;line-height: 30px; margin: 3px 15px; display: flex;">
                    <div style="width: 100px; line-height: 28px; "><b>工位: </b></div>
                    <el-autocomplete v-model="audit['cub']" placeholder="请输入工位" @change="auditCubCg"
                     :fetch-suggestions="queryAuditCub" style="line-height: 30px; height: 30px; width: 260px;"></el-autocomplete>
                </div>
                <div style="height: 30px;line-height: 30px; margin: 3px 15px; display: flex;">
                    <div style="width: 100px; line-height: 28px; "><b>时间: </b></div>
                    <el-date-picker v-model="audit['time']" style="line-height: 30px; height: 30px; width: 260px;"
                      type="datetime" placeholder="选择日期时间">
                    </el-date-picker>
                </div>
                <div style="height: 30px;line-height: 30px; margin: 3px 15px; display: flex;">
                    <div style="width: 100px; line-height: 28px; "><b>备注: </b></div>
                    <el-autocomplete v-model="audit['note']" placeholder="请输入备注" @change="auditNoteCg"
                     :fetch-suggestions="queryAuditNote" style="line-height: 30px; height: 30px; width: 360px;"></el-autocomplete>
                </div>
            </div>
        </div>

        <div class="right">
            <div style="line-height: 25px; font-size: 18px; display: flex; justify-content: space-between;">
                <b>当前文件列表</b>
                <el-button type="primary" @click="btnChange('files')" style="font-size: 15px; height: 25px; width:80px;
                 border-radius: 10px; padding: 0;border: none;"><b>打开文件夹</b></el-button>
            </div>

            <div class="files" style="height: 360px; margin: 0; overflow-y: scroll; box-shadow: 0 2px 4px rgba(0, 0, 0, .12), 0 0 6px rgba(0, 0, 0, .04);">
                <input type="file" id="files" hidden @change="fileChange" webkitdirectory>
                <div class="each" v-for="(f,i) in files" style="height: 25px; line-height: 25px; font-size: 20px;">
                    <div :class="i == presentIdx? 'chosen': 'unchosen'">
                        <span style="line-height: 25px;" v-if="i == presentIdx">{{f.name}}</span>
                        <span style="line-height: 25px;" v-else @click="presentChange(f, i)">{{f.name}}</span>
                    </div>
                </div>
            </div>

            <div style="display: flex; justify-content: space-around; margin-top: 10px;height: 40px;line-height: 40px;">
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
                <div style="line-height: 20px; font-size: 16px; ">当前检测进度</div>
                <el-progress :percentage="50" style="line-height: 30px; font-size: 22px;"></el-progress>
            </div>
        </div>
    </div>
</template>

<script>
    export default {
        name: "fog",
        data(){
            return{
                audit:{
                    'person':'', 'cub':'', 'time':this.timeNow, 'note':''
                },
                dest_dir:'',
            }
        },
        methods:{
            detectOne(){
                console.log('进行单个视频检测')

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
                // if(this.audit['person'] == '' || this.audit['cub']=='' || this.audit['time']==''){
                //     this.$message({
                //       showClose: true,
                //       message: '请完善质检人员信息！',
                //       type: 'error',
                //       center: true
                //     });
                //     return
                // }

                // 将数据传入后端，参数如下：
                // type：使用的算法类型，fog(空调漏氟)，tv(电视机回收)
                // files[]：视频文件列表
                // idx：当前视频文件的索引
                // audit：审计人员信息
                // dest_dir: 保存地址
                let formdata = new FormData();
                formdata.append('type', this.detectType)
                formdata.append('idx', this.presentIdx)
                formdata.append('dest_dir', './results')

                for (var key in this.audit){
                    // console.log(key, this.audit[key])
                    formdata.append('audit[]', this.audit[key])
                }

                for(var k in this.files){
                        formdata.append('files[]', this.files[k])
                        // console.log(this.files[k])
                    }

                const config = {
                    headers: {
                      'Content-Type': 'multipart/form-data'
                    }
                  }

                var name = this.files[this.presentIdx]['name'].split('.')[0]
                var date = new Date()
                var time = String(date.getFullYear())+"/"+String(date.getMonth())+'/'+String(date.getDate())

                this.axios.post('/video/detect', formdata, config)
                .then((response) => {
                    // console.log(response.data)
                    const blob = new Blob([response.data], {'type': 'text/html'})
                    const blobUrl = window.URL.createObjectURL(blob)
                    this.$store.commit('htmlChange', [blobUrl, name, 'text/html', time])
                })
                .catch((error) => {
                    console.log(error)
                })
            },

            async detectMul(){
                console.log('进行多个视频检测')
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
                if(this.audit['person'] == '' || this.audit['cub']=='' || this.audit['time']==''){
                    this.$message({
                      showClose: true,
                      message: '请完善质检人员信息！',
                      type: 'error',
                      center: true
                    });
                    return
                }

                const config = {
                    headers: {
                      'Content-Type': 'multipart/form-data'
                    }
                }

                // 变量当前视频文件列表，依次进行检测并获取检测结果html
                for(var i = 0; i < this.files.length; i++){
                    // console.log('i:', i)
                    let formdata = new FormData();
                    formdata.append('type', this.detectType)
                    formdata.append('idx', i)
                    formdata.append('dest_dir', './results')
                    for (var key in this.audit){
                        // console.log(key, this.audit[key])
                        formdata.append('audit[]', this.audit[key])
                    }

                    for(var k in this.files){
                        formdata.append('files[]', this.files[k])
                    }

                    var name = this.files[i]['name'].split('.')[0]
                    var date = new Date()
                    var time = String(date.getFullYear())+"/"+String(date.getMonth())+'/'+String(date.getDate())

                    await this.axios.post('/video/detect', formdata, config)
                    .then((response) => {
                        // console.log(this.files)
                        const blob = new Blob([response.data], {'type': 'text/html'})
                        const blobUrl = window.URL.createObjectURL(blob)

                        this.$store.commit('htmlChange', [blobUrl, name, 'text/html', time])
                    }).catch((error) => {
                        console.log(error)
                    })
                }
            },

            async fileChange(e) {
              try {
                const fu = document.getElementById(this.id)
                if (fu == null) return

                //  如果是选择单个文件，则根据文件类型进行页面跳转，同时更新最近的文件
                //  在视频检测页面可以同时添加多个视频文件
                if(this.id == 'file'){
                    var files = fu.files
                    console.log('这是files：', files)

                    for(let i = 0; i < files.length; i++){
                        var mfile = files[i]
                        console.log(mfile.path)
                        let url = window.webkitURL.createObjectURL(mfile) ;
                        mfile['url'] = url
                        var date = new Date()
                        var time = String(date.getFullYear())+"/"+String(date.getMonth())+'/'+String(date.getDate())
                        mfile['time'] = time
                        this.$store.commit('fileChange', mfile)

                        // 将文件发送到后端进行上传
                        let formdata = new FormData();
                        formdata.append('files[]', mfile);
                        formdata.append('type', this.$store.state.detectType);
                        await this.axios.post('/video/add', formdata,{headers: {'Content-Type': 'multipart/form-data'}})
                        .then((response) => {
                            console.log(response.data)
                        })
                        .catch((error) => {
                            console.log(error)
                        })
                    }
                }// 如果是打开视频文件夹，就跳转到视频检测页面，同时更新最近的文件
                else if(this.id == 'files')
                {
                    var files = [];

                    for(let index = 0; index < fu.files.length; index++){
                        // 只将当前文件夹下的视频文件添加进去
                        if(fu.files[index].type == "video/mp4")
                        {
                            let url = window.webkitURL.createObjectURL(fu.files[index]) ;
                            fu.files[index]['url'] = url
                            files.push(fu.files[index])

                            let formdata = new FormData();
                            formdata.append('files[]', fu.files[index]);

                            // 将文件发送到后端进行上传
                            await this.axios.post('/video/add', formdata,{headers: {'Content-Type': 'multipart/form-data'}})
                            .then((response) => {
                                console.log(response.data)
                            })
                            .catch((error) => {
                                console.log(error)
                            })
                        }
                    }
                    this.$store.commit('folderChange', files)
                }
                else{
                    console.log('dest button按钮')
                    console.log(fu.files)
                    this.dest_dir = '目标路径'
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
                this.$store.commit('presentVideoChange', [f, i])
            },

            auditPersonCg(){
                // console.log('审计人员改变')
                this.$store.commit('auditChange', ['person', this.audit['person']])
            },
            auditCubCg(){
                // console.log('审计人员改变')
                this.$store.commit('auditChange', ['cub', this.audit['cub']])
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
            queryDestDir(queryString, callback){
                var res = [{"value":this.$store.state.audit['note']}]
                callback(res)
            },
        },
        computed:{
            // 当前视频文件
            present(){
                return this.$store.state.presentVideo
            },
            presentIdx(){
                return this.$store.state.presentVideoIdx
            },
            detectType(){
                return this.$store.state.detectType
            },
            files:{
                get(){
                    return this.$store.state.videoList
                },
            },
            videoEmpty(){
                    return this.$store.state.presentVideo == null
            },
            url() {
                return this.present['url']
            },
            timeNow(){
                const t = new Date();
                return new Date(t.getFullYear(), t.getMonth(), t.getDate(), t.getHours(), t.getMinutes(), t.getSeconds())
            },
        },
        watch:{
            present(newVal, oldVal){
                // console.log('视频页面的视频文件被修改了', oldVal, newVal)
            },
            presentIdx(newVal, oldVal){
                // console.log('视频文件的idx被修改了', oldVal, newVal)
            },
            files(newVal, oldVal){
                console.log('视频文件列表files发生了修改')
            }
        }
    }
</script>

<style scoped>
.wrap{
    /*box-shadow: 0 2px 4px rgba(0, 0, 0, .12), 0 0 6px rgba(0, 0, 0, .04);*/
    display: flex;
    justify-content: space-between;
    width: 910px;
    height: 520px;
    /*margin: auto;*/
}

.left{
    /*width: 860px;*/
    /*height: 680px;*/

    width: 645px;
    height: 520px;
    /*background-color: #666666;*/
}

.right{
    /*width: 320px;*/
    /*height: 680px;*/

    width: 245px;
    height: 520px;
    /*background-color: #B3C0D1;*/
}

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

.el-autocomplete {
    min-height: 28px;
}

::v-deep .el-autocomplete .el-input  .el-input__inner{
    min-height: 30px;
    height: 30px;
}

::v-deep .el-date-editor .el-input__inner{
    min-height: 30px;
    height: 30px;
}
</style>