<template>
    <div class="wrap">
        <div class="left">
            <div style="line-height: 25px; font-size: 18px; height: 25px; text-overflow: ellipsis; width: 100%;">
                <b>当前结果文件:&nbsp;</b>{{present}}
            </div>

            <div class="html" style="width: 100%;height: 495px; line-height: 495px;">
                <table class="details" style="display: block; padding: 15px;">
                    <tr v-for="(value, key) in details">
                      <td class="key">{{key}}:</td>
                      <td class="value">{{value}}</td>
                    </tr>
                </table>

                <table class="result" style="display: block; padding-left: 15px;">
                    <tr>
                        <th>序号</th>
                        <th>操作时间段</th>
                        <th>操作时间点</th>
                        <th>视频时间点</th>
                        <th>系统判断结果</th>
                        <th>判断图像</th>
                    </tr>
                    <tr>
                        <td v-for="res in results" >{{res}}</td>
                        <td><img src="" alt="无图像"></td>
                    </tr>
                </table>
            </div>
        </div>

        <div class="right">
            <div style="line-height: 25px; font-size: 18px; height: 25px; display: flex; justify-content: space-between;">
                <b>当前文件列表</b>
            </div>

            <div class="files" style="margin: 0; overflow: scroll; width: 100%; height: 470px;
                 box-shadow: 0 2px 4px rgba(0, 0, 0, .12), 0 0 6px rgba(0, 0, 0, .04);">
                <div class="each" v-for="(f,i) in fileNames" style="height: 25px; line-height: 25px; font-size: 18px;">
                    <div :class="i == presentIdx? 'chosen': 'unchosen'">
                        <span style="line-height: 25px; white-space: nowrap;" v-if="i == presentIdx">{{f}}</span>
                        <span style="line-height: 25px; white-space: nowrap;" v-else @click="presentChange(f, i)">{{f}}</span>
                    </div>
                </div>
            </div>

            <div style="line-height: 25px; height: 25px; display: flex; justify-content: center;">
                <el-button type="primary" round @click="exportExcel">导出excel文件</el-button>
            </div>
        </div>
    </div>
</template>

<script>
    export default {
        name: "result",
        data(){
            return{
                id:'file',
            }
        },
        methods:{
            presentChange(f, i){
                console.log('当前结果文件发生切换')
                this.$store.commit('presentResultChange', [f, i])
                this.getResult(this.present)
            },

            // TODO:从后台根据文件名获取指定结果信息
            getResult(name){
                console.log('尝试获取结果文件:'+name)
                this.axios({
                    method:'post',
                    url:'/result',
                    data:{'name': name}
                }).then(res=>{
                    console.log(res.data)
                    this.$store.commit('presentResultInfoChange', [res.data.details, res.data.results])
                }).catch(err=>{
                    console.log(err)
                })
            },

            // TODO：导出excel文件接口（向后端发送请求，参数：当前结果文件name）
            exportExcel(){
              console.log('导出excel文件')
            },
        },
        computed:{
            present(){
                console.log(this.$store.state.presentResult)
                return this.$store.state.presentResult
            },
            presentIdx(){
                return this.$store.state.presentResultIdx
            },
            fileNames(){
                return this.$store.state.resultList
            },
            details(){
                return this.$store.state.presentResultInfo['details']
            },
            results(){
                return this.$store.state.presentResultInfo['results']
            }

        },
        created() {
            // 当打开结果界面时，从后端获取当前结果文件
            if(this.fileNames.length > 0){
                this.getResult(this.present)
            }
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
    /*box-shadow: 0 2px 4px rgba(0, 0, 0, .12), 0 0 6px rgba(0, 0, 0, .04);*/
    width: 645px;
    height: 520px;
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

table {
    border-collapse: collapse;
}

.detail td, .detail th {
    padding: 4px;
}

.key {
    font-weight: bold;
    text-align: right;
    height: 25px;
    line-height: 25px;
    font-size: 16px;
}

.value{
    text-align: right;
    line-height: 25px;
    font-size: 16px;
}

.result td, .result th {
    border: 1px solid #efefef;
    text-align: left;
    padding: 8px;
    height: 40px;
    line-height: 40px;
}

img {
    width: 400px;
}

</style>