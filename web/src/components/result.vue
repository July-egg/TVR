<template>
    <div class="wrap">
        <div class="left">
            <div class="video" style="height: 100%; width: 645px;margin: 0;">
                <!--     打开视频文件页面      -->
                <div @click="btnChange('file')" style="width:100%; height:100%; object-fit:fill; display: flex;
                     box-shadow: 0 2px 4px rgba(0, 0, 0, .12), 0 0 6px rgba(0, 0, 0, .04);" v-if="htmlEmpty">
                    <input type="file" id="file" hidden @change="fileChange" accept="text/html" multiple="multiple">
                    <div style="display: flex; justify-content: space-around; align-content: center;margin: auto;">
                        <i class="el-icon-plus" style="font-size: 40px; line-height: 45px;"></i>
                        <span style="font-size: 40px; line-height: 45px;">&nbsp;&nbsp;打开结果文件</span>
                    </div>
                </div>

                <div class="else" style="width:100%; height:650px; object-fit:fill;" v-else>
                    <div style="line-height: 35px; font-size: 20px; height: 35px; text-overflow: ellipsis; width: 100%;">
                        <b>当前结果文件:&nbsp;</b>空调二线抽氟工位_16B27158_1669259154_1.mp4
                    </div>
                     <iframe :src="present" style="width:100%; height:100%; object-fit:fill;" scrolling="auto"></iframe>
<!--                     <iframe src="/static/summary.html" style="width:100%; height:100%; object-fit:fill;" scrolling="auto"></iframe>-->
                </div>
            </div>
        </div>

        <div class="right">
            <div style="line-height: 25px; font-size: 18px; display: flex; justify-content: space-between;">
                <b>当前文件列表</b>
<!--                <el-button type="primary" icon="el-icon-plus" @click="btnChange('files')"-->
<!--                  style="font-size: 15px; height: 25px; width:30px; border-radius: 10px; padding: 0;border: none;"></el-button>-->
            </div>
            <div class="files" style="margin: 0; overflow: scroll; width: 100%; height: 495px;
                 box-shadow: 0 2px 4px rgba(0, 0, 0, .12), 0 0 6px rgba(0, 0, 0, .04);">
                <input type="file" id="files" hidden @change="fileChange" webkitdirectory>
                <div class="each" v-for="f in files" style="height: 25px; line-height: 25px; font-size: 18px;">
                    <div :class="f['idx'] == presentIdx? 'chosen': 'unchosen'">
                        <span style="line-height: 25px; white-space: nowrap;" v-if="f['idx'] == presentIdx">{{f['name']}}</span>
                        <span style="line-height: 25px; white-space: nowrap;" v-else @click="presentChange(f)">{{f['name']}}</span>
                    </div>
                </div>
            </div>
        </div>
    </div>
</template>

<script>
    export default {
        name: "result",
        data(){
            return{
                id:'file'
            }
        },
        methods:{
            fileChange(e) {
              try {
                const fu = document.getElementById(this.id)
                if (fu == null) return

                //  如果是选择单个文件，则根据文件类型进行页面跳转，同时更新最近的文件
                if(this.id == 'file'){
                    var files = fu.files
                    console.log(files)

                    for(let i = 0; i < files.length; i++){
                        var mfile = files[i]
                        let url = window.webkitURL.createObjectURL(mfile) ;
                        mfile['url'] = url
                        this.$store.commit('fileChange', mfile)
                    }
                }
                // 打开文件夹
                else
                {
                    var files = [];

                    for(let index = 0; index < fu.files.length; index++){
                        if(fu.files[index].type == "text/html")
                        {
                            let url = window.webkitURL.createObjectURL(fu.files[index]) ;
                            fu.files[index]['url'] = url
                            files.push(fu.files[index])
                        }
                    }
                    console.log(files)
                    this.$store.commit('folderChange', files)
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
            presentChange(f){
                console.log('当前结果文件发生切换')
                console.log(f)
                this.$store.commit('presentHtmlChange', f)
            },
            getResults(){
                const blob = new Blob([response.data], {'type': 'text/html'})
                const blobUrl = window.URL.createObjectURL(blob)
                this.$store.commit('htmlSrcChange', blobUrl)
                console.log(blobUrl)
            },
        },
        computed:{
            // 当前视频文件
            present(){
                console.log(this.$store.state.presentHtml)
                return this.$store.state.presentHtml
            },
            presentIdx(){
                return this.$store.state.presentHtmlIdx
            },
            files:{
                get(){
                    return this.$store.state.htmlList
                },
            },
            htmlEmpty(){
                    // return false
                    return this.$store.state.presentHtml == null
            },
            htmlSrc(){
                // this.axios({
                //     method:"get",
                //     url:'/result',
                // })
                // .then((response) => {
                //     console.log(response)
                // })
                // .catch((error) => {
                //     console.log(error)
                // })


                // return this.$store.state.htmlSrc
            },

        },
        watch:{
            htmlSrc(newVal, oldVal){
                console.log('htmlSrc被修改了', oldVal, newVal)
            },
        },
        created() {

        }
    }
</script>

<style scoped>
.wrap{
    /*box-shadow: 0 2px 4px rgba(0, 0, 0, .12), 0 0 6px rgba(0, 0, 0, .04);*/
    display: flex;
    justify-content: space-between;
}

.left{
    box-shadow: 0 2px 4px rgba(0, 0, 0, .12), 0 0 6px rgba(0, 0, 0, .04);
    width: 645px;
    height: 520px;
    /*background-color: #666666;*/
    /*overflow-scrolling: auto;*/
}

.right{
    /*box-shadow: 0 2px 4px rgba(0, 0, 0, .12), 0 0 6px rgba(0, 0, 0, .04);*/
    width: 245px;
    height: 520px;
    /*background-color: #B3C0D1;*/
}

.each .unchosen:hover{
    background-color: #cce8ff;
    opacity: 0.5;
}

.chosen{
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
</style>