<template>
    <div class="wrap">
        <div class="begin">
            <div class="head"><b>开始使用</b></div>

            <div class="bfile" @click="btnChange('file')">
                <input type="file" id="file" hidden @change="fileChange" accept=".mp4, .json">

                <div class="icon">
                   <i class="el-icon-edit-outline" style="font-size: 45px; margin: 10px; color: black;"></i>
                </div>
                <div class="info">
                    <p style="display: flex; justify-content: space-between; width: 263px; line-height: 38px; margin: 0;">
                        <span style="display:inline-block; float: left; line-height: 38px; font-size: 20px;">
                            <b>打开文件</b>
                        </span>
                    </p>
                    <p style="line-height: 30px; margin: 0">
                        <span style="float: left;  line-height: 30px;">
                            选择.mp4文件或.html格式文件打开
                        </span>
                    </p>
                </div>
            </div>

            <div class="bfile" @click="btnChange('files')">
                <input type="file" id="files" hidden @change="fileChange" webkitdirectory>

                <div class="icon">
                   <i class="el-icon-folder-opened" style="font-size: 45px; margin: 10px; color: black;"></i>
                </div>
                <div class="info">
                    <p style="display: flex; justify-content: space-between; width: 263px; line-height: 38px; margin: 0;">
                        <span style="display:inline-block; float: left; line-height: 38px; font-size: 20px;">
                            <b>打开文件夹</b>
                        </span>
                    </p>
                    <p style="line-height: 30px; margin: 0">
                        <span style="float: left;  line-height: 30px;">
                            选择一个视频文件夹并打开
                        </span>
                    </p>
                </div>
            </div>
        </div>

        <div class="recent">
            <div class="head"><b>最近使用的文件</b></div>
            <div class="file" v-for="f in recentFiles" @click="openRecent(f)">
                <div class="icon">
                   <i class="el-icon-video-play" style="font-size: 45px; margin: 8px; color: black;" v-if="f.type=='video/mp4'"></i>
                   <i class="el-icon-files" style="font-size: 45px; margin: 8px; color: black;" v-else></i>
                </div>
                <div class="info">
                    <p style="display: flex; justify-content: space-between; width: 283px; line-height: 38px; margin: 0;">
                        <span style="display:inline-block; text-overflow: ellipsis; float: left; line-height: 38px; font-size: 18px;
                                    width:220px; overflow: hidden;">
                            {{f.name}}
                        </span>
                        <span style="display:inline-block; float: right;line-height: 38px; font-size: 16px;
                                     overflow: hidden; width: 80px;">
                            {{f.time}}
                        </span>
<!--                        <span style="display:inline-block; float: right;line-height: 50px; font-size: 18px;-->
<!--                                     overflow: hidden; width: 105px;" v-if="f.type=='video/mp4'">-->
<!--                            {{f.lastModifiedDate.getFullYear()}}/{{f.lastModifiedDate.getMonth()}}/{{f.lastModifiedDate.getDate()}}-->
<!--                        </span>-->
                    </p>
                </div>
            </div>
        </div>
    </div>
</template>

<script>
export default {
    name: "home",
    data(){
        return{
            // 最近的文件列表
            recentFiles:[],
            id:'file'  // 当前是打开单个文件还是文件夹
        }
    },
    methods:{
        loadFiles(){
            this.recentFiles = this.$store.state.recentFiles;
        },
        openRecent(file){
            console.log(file);
            // 根据文件类型，判断是跳转到video还是result界面
            if (file.type == 'video/mp4'){
                console.log('选择的文件是mp4类型')
                this.$store.commit('openRecent', file)
                this.$store.commit('pageChange', '2')
            }
            else{
                console.log('选择的文件是html类型')
                this.$store.commit('openRecent', file)
                this.$store.commit('pageChange', '3')
            }
        },

        fileChange(e) {
          //  在文件夹页面中具体选择一个文件或者文件夹
          try {
            const fu = document.getElementById(this.id)
            if (fu == null) return

            //  如果是选择单个文件，则根据文件类型进行页面跳转，同时更新最近的文件
            if(this.id == 'file'){
                var file = fu.files[0]
                let url = window.webkitURL.createObjectURL(file) ;
                file['url'] = url

                if(file.type == "video/mp4"){
                    console.log('选择的文件是mp4类型')
                    this.$store.commit('fileChange', file)
                    this.$store.commit('pageChange', '2')
                }
                else if(file.type == 'text/html'){
                    console.log('选择的文件是html类型')
                    this.$store.commit('fileChange', file)
                    this.$store.commit('pageChange', '3')
                }else{
                    console.error("选择的文件应是.mp4或者.html类型");
                }
            }
            // 如果是打开视频文件夹，就跳转到视频检测页面，同时更新最近的文件
            else
            {
                var files =[]
                for(let index = 0; index < fu.files.length; index++){
                    if(fu.files[index].type == "video/mp4")
                    {
                        let url = window.webkitURL.createObjectURL(fu.files[index]) ;
                        fu.files[index]['url'] = url
                        files.push(fu.files[index])
                    }
                }
                console.log(files)
                this.$store.commit('folderChange', files)
                this.$store.commit('pageChange', '2')
            }

          } catch (error) {
            console.debug('choice file err:', error)
          }
        },
        btnChange(id) {
            // 打开文件夹页面进行选择
            this.id = id
            var file = document.getElementById(id)
            file.click()
        },
    },
    mounted() {
        this.loadFiles();
    }

}
</script>

<style scoped>
.wrap{
    box-shadow: 0 2px 4px rgba(0, 0, 0, .12), 0 0 6px rgba(0, 0, 0, .04);
    display: flex;
    justify-content: space-around;
}

/* 最近使用的文件 */
.recent{
    /*width: 500px;*/
    /*height: 680px; */
    width: 375px;
    height: 520px;
}

.head{
    font-size: 25px;
    /*height: 50px;*/
    /*width: 400px;*/
    height: 38px;
    width: 300px;
    line-height: 50px;
    /*上右下左*/
    margin: 30px 0px 30px 40px;
}

.file{
    /*height: 100px;*/
    height: 75px;
    /*line-height: 80px;*/
    line-height: 60px;
    /*width: 450px;*/
    width: 338px;
    margin: 10px 0 10px 40px;
    display: flex;
    justify-content: space-between;
}

.bfile{
    /*height: 100px;*/
    /*line-height: 80px;*/
    /*width: 450px;*/
    /*margin: 10px 0 10px 40px;*/
    height: 75px;
    line-height: 60px;
    width: 338px;
    margin: 7px 0 7px 30px;
    display: flex;
    justify-content: space-between;
}
/* 开始使用 */
.begin{
    /*width: 500px;*/
    /*height: 680px;*/
    width: 375px;
    height: 520px;
}
</style>