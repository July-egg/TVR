import Vue from 'vue'
import Vuex from 'vuex'
import fi from "element-ui/src/locale/lang/fi";
import {isUndefined} from "element-ui/src/utils/types";
import fa from "element-ui/src/locale/lang/fa";

Vue.use(Vuex)

// state：保存状态(共享变量)
const state = {

    // login页面需要保存的变量
    username:'admin',
    password:'12345678',

    //homepage页面，默认为电视机检测页面
    pageIndex:'1-2', // 当前page索引值：1-1、1-2、2

    // home页面需要保存的变量
    recentFiles:[], // 最近使用的文件，json与video混杂


    // 视频页面需要保存的变量
    videoType:'tv', // 视频检测类型，tv or fog
    presentTv: null, // 当前视频文件，跳转到视频检测页面
    presentTvIdx: -1, // 当前视频文件在文件列表中的索引
    tvList:[], // 记录当前视频文件列表

    presentFog: null, // 当前视频文件，跳转到视频检测页面
    presentFogIdx: -1, // 当前视频文件在文件列表中的索引
    fogList:[], // 记录当前视频文件列表

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
        if(i == '1-1'){
            state.videoType = 'fog'
        }
        if(i == '1-2'){
            state.videoType = 'tv'
        }
        console.log('当前是page', state.pageIndex, state.videoType)
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
        // 审计人员信息保存
        state.audit[type] = val
    },
    // folderChange(state, f){
    //     // 更新当前视频列表文件夹，之前已经打开的视频文件被覆盖，仅限视频检测页面使用
    //     state.presentFolder = f
    //     state.videoList = f
    //     state.presentVideo = f[0]
    //     state.presentVideoIdx = 0
    //     this.commit('recentChange', f)
    // },
    fileChange(state, [f, type]) {
        // 将视频文件根据类型添加到对应的列表中
        if(type == 'tv'){
            state.tvList.push(f)
            state.presentTv = f
            state.presentTvIdx = state.tvList.length - 1
        }
        else{
            state.fogList.push(f)
            state.presentFog = f
            state.presentFogIdx = state.fogList.length - 1
        }
    },
    presentVideoChange(state, [f, i, type]) {
        // 当前视频文件进行切换，即更新索引idx
        if(type == 'tv'){
            state.presentTv = f
            state.presentTvIdx = i
        }else{
            state.presentFog = f
            state.presentFogIdx = i
        }
    },
    deleteVideo(state, [i, type]){
        if(type=='tv'){
            state.tvList.splice(i, 1)
            if(i==state.presentTvIdx){
                state.presentTvIdx = state.tvList.length - 1
            }else if(i < state.presentTvIdx){
                state.presentTvIdx = state.presentTvIdx-1
            }
            state.presentTv = state.tvList[state.presentTvIdx]
        }else{
            state.fogList.splice(i, 1)
            if(i==state.presentFogIdx){
                state.presentFogIdx = state.fogList.length - 1
            }else if(i < state.presentFogIdx){
                state.presentFogIdx = state.presentFogIdx-1
            }
            state.presentFog = state.fogList[state.presentFogIdx]
        }
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
const actions = {
    fileChangeA(context, [f, type]){
        if(type=='tv'){
            if (state.tvList.find(function (value) {return value.name == f.name})) {
                alert('文件'+f.name+'已在视频列表中！')
                return false
            }
            context.commit('fileChange', [f, type])
        }else{
            if (state.fogList.find(function (value) {return value.name == f.name})) {
                alert('文件'+f.name+'已在视频列表中！')
                return false
            }
            context.commit('fileChange', [f, type])
        }
        return true
    }
}

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
