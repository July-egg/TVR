import Vue from 'vue'
import Vuex from 'vuex'
import fi from "element-ui/src/locale/lang/fi";

Vue.use(Vuex)

// state：保存状态(共享变量)
const state = {

    // login页面需要保存的变量
    username:'admin',
    password:'12345678',

    //homepage页面，默认为首页
    pageIndex:'1', // 当前page索引值：1、2-1、2-2、3

    // home页面需要保存的变量
    recentFiles:[], // 最近使用的文件，json与video混杂
    detectType:'tv',

    // video页面需要保存的变量
    presentFolder:[], // 当前打开的文件夹，在视频检测页面使用
    presentVideo: null, // 当前视频文件，跳转到视频检测页面
    presentVideoIdx: -1, // 当前视频文件在文件列表中的索引
    videoList:[], // 记录当前视频文件列表

    // 审查人员信息字典
    audit:{
        'person':'', 'cub':'', 'time':'', 'note':''
    },

    // result页面需要保存的变量
    htmlList:[], // 记录当前视频文件列表
    presentHtml: null, // 当前json文件，跳转到结果统计页面
    presentHtmlIdx: -1, // 当前json文件在文件列表中的索引
}

// mutations：定义一些方法(默认传入一个state参数)，对状态进行修改
//   注：mutations中的方法必须是同步方法，mutation是修改state的唯一途径
const mutations = {
    // login页面
    userChange(state, user){
        state.username = user
    },
    pwdChange(state, pwd){
        state.password = pwd
    },

    //homepage
    pageChange(state, i){
        state.pageIndex = String(i)
        if(i == '2-1'){
            state.detectType = 'air'
        }
        if(i == '2-2'){
            state.detectType = 'tv'
        }
        console.log('当前是page', state.pageIndex, state.detectType)
    },

    // home页面
    recentChange(state, files){
        // 最近使用的文件列表，控制最大数量为5
        if(files.length >= 5){
            var t = []
            for(let i = 0; i <5;i++){
                t.unshift(files[i])
            }
            state.recentFiles = t
        }
        else{
            for(let i = 0; i < files.length; i++){
                state.recentFiles.unshift(files[i])
            }
            while(state.recentFiles.length > 5){
                state.recentFiles.pop()
            }
        }
        // console.log('recent files: \n', state.recentFiles)
    },

    folderChange(state, f){
        // 更新当前视频列表文件夹，之前已经打开的视频文件被覆盖，仅限视频检测页面使用
        state.presentFolder = f
        state.videoList = f
        state.presentVideo = f[0]
        state.presentVideoIdx = 0
        this.commit('recentChange', f)
    },
    fileChange(state, f) {
        // fileChange函数的使用：首页单击最近使用的文件时跳转(一个)，视频页面添加新的视频文件(可以多个)
        // 将视频文件添加到文件列表末尾，同时更新当前文件的索引idx。
        if(f.type=='video/mp4'){
            state.presentVideo = f
            state.videoList.push(f)
            state.presentVideoIdx = state.videoList.length - 1
        }else{
            state.presentHtml = f
            state.htmlList.push(f)
            state.presentHtmlIdx = state.htmlList.length - 1
        }
        this.commit('recentChange', [f])
    },
    openRecent(state, f){
        // 打开最近使用的文件，根据
        if(f.type=='video/mp4'){
            state.videoList = [f]
            state.presentVideo = f
            state.presentVideoIdx = 0
        }else{
            // state.htmlList = [f]
            state.presentHtml = f['url']
            state.presentHtmlIdx = f['idx']
        }
    },

    // video页面
    auditChange(state, [type, val]){
        state.audit[type] = val
    },
    presentVideoChange(state, [f, i]) {
        // 当前视频文件/html文件进行切换，即更新索引idx
        if(f.type=='video/mp4'){
            state.presentVideo = f
            state.presentVideoIdx = i
        }else{
            state.presentHtml = f
            state.presentHtmlIdx = i
        }
        // this.commit('recentChange', [f])
        },

    // result页面
    htmlChange(state, [url, name, type, time]){
        // 新增html文件
        console.log('新增结果html文件:', name)
        state.presentHtml = url
        state.presentHtmlIdx = state.htmlList.length
        var f = {'url':url, 'name':name, 'type':type, 'idx':state.presentHtmlIdx, 'time':time}
        state.htmlList.push(f)
        state.recentFiles.push(f)
    },
    presentHtmlChange(state, f){
        // 当前结果html文件的webkitURL地址
        state.presentHtml = f['url']
        state.presentHtmlIdx = f['idx']
    }

}

// actions类似于mutations，但是是用来替代其进行异步操作的。
// 其中函数的默认参数：context: 上下文(相当于store) 只能通过修改mutation间接改变state，而不能直接改
// actions中也可以传递参数，方法与mutations相同
const actions = {}

//准备getters对象——用于将state中的数据进行加工
const getters = {
    bigSum(){
        return state.sum * 10
    }
}

export default new Vuex.Store({
  state,
  mutations,
  actions,
  getters
})
