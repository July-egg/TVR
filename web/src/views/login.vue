<template>
    <div class="login">
      <meta name="viewport" content="width=device-width,initial-scale=1, maximum-scale=1, user-scalable=yes">

      <div class="header">
        <img src="../assets/image/logo_cut.png" alt="系统logo">
        <span style="padding-left:.5rem;"><b>废旧电器回收智能管理平台</b></span>
      </div>

      <div class="center">
            <div class="input">
                <div><h3 style="font-size: .7rem;color: #ffffff; padding-bottom: .25rem">用 户 登 录</h3></div>

                <div class="user" style="display: flex; height: 2rem; width: 10rem; margin: 0; justify-content: center;">
                    <i class="el-icon-user" style="font-size: 1rem; margin-right: .625rem;"></i>
                    <el-autocomplete v-model="user" placeholder="请输入用户名" @change="userCg" style="width: 8rem; height: 1rem;"
                              :fetch-suggestions="queryUsr" @select="handleSelectUsr"></el-autocomplete>
                </div>
                <div class="user" style="display: flex; height: 2rem; width: 10rem; margin: 0; justify-content: center;">
                    <i class="el-icon-lock" style="font-size: 1rem; margin-right: .625rem;"></i>
                    <el-autocomplete v-model="pwd" placeholder="请输入密码" @change="pwdCg" style="width: 8rem; height: 1rem;"
                              :fetch-suggestions="queryPwd" @select="handleSelectPwd" type="password"></el-autocomplete>
                </div>
            </div>

            <div class="log">
                <button style="color: #ffffff;background-color: #4095E5;font-size:.5rem;width: 3.5rem; margin: auto;
                        border-radius:.25rem;  border: none; padding: 1%;" @click="login">
                    登 录
                </button>
            </div>
      </div>

      <div class="footer">
        <span style="color: #ffffff; display: flex; justify-content: center; font-size: .375rem; margin: auto;">
            <b>—————————•&nbsp;&nbsp;&nbsp;</b>深 圳 爱 析 科 技 有 限 责 任 公 司<b>&nbsp;&nbsp;&nbsp;•—————————</b>
        </span>
      </div>
    </div>
</template>

<script>
export default {
    name: "login",
    data(){
        return{
            user:'',
            pwd:'',
            htmlHeight: {
              height: '300px'
            }
        }
    },
    methods:{
        login(){
            console.log('登录')
            this.$router.push('/home')
        },
        userCg(){
            console.log('用户名改变')
            this.$store.commit('userChange', this.user)
        },
        pwdCg(){
            console.log('密码改变')
            this.$store.commit('pwdChange', this.pwd)
        },
        queryUsr(queryString, callback){
            var res = [{"value":this.$store.state.username}]
            callback(res)
        },
        queryPwd(queryString, callback){
            var res = [{"value":this.$store.state.password}]
            callback(res)
        },
        handleSelectUsr(item){
            console.log(item)
        },
        handleSelectPwd(item){
            console.log(item)
        },
        getHtmlHeight () {
          let htmlHeight = window.innerHeight + 'px'
          this.$set(this.htmlHeight, 'height', htmlHeight)
        }
    },
    mounted() {
      this.getHtmlHeight()
    }

}
</script>

<style scoped>

.login{
    //width: 1080px;
    //height: 645px;
    width: 100%;
    height: 100%;
    line-height: 100%;
    background: url("../assets/image/login.jpg") top center no-repeat;
    background-size:cover;
    align-items: center;
    justify-content: center;

    vertical-align: middle;
    text-align: center;
    display: flex;
    flex-direction: column;
    box-sizing: border-box;
}

/* 头部样式起始处 */
.header{
  width: 100%;
  height: 20%;
  display: flex;
  align-items: center;
  justify-content: center;
  padding-top: .5rem;
  font: normal 1.25rem Cookie, Noto Sans, Helvetica, sans-serif;
  font-family: sans-serif;;
  color: #ffffff;
}

.header img{
    height: 2rem;
    width: 2rem;
}

/*中部样式起始处*/
.center{
    width: 100%;
    height: 50%;
    padding: 1rem 0 0 0;
    align-items: center;
    justify-content: center;
    display: flex;
  flex-direction: column;
}

.center .input{
    width: 45%;
    height: 65%;
    background-color: rgba(177, 203, 238, .6);
    border-radius: 1rem;
    padding: 1% 0 ;
    margin: auto;
    //vertical-align: middle;
    text-align: center;
    align-items: center;
    justify-items: center;
  justify-content: space-evenly;
    display: flex;
    flex-direction: column;
}

.center .log{
    width: 45%;
    height: 35%;
    border-radius: 1rem;
    padding: 1% 0 ;
    text-align: center;
    align-items: center;
    justify-items: center;
    display: flex;
    flex-direction: column;
}

/*底部样式起始处*/
.footer{
    width: 100%;
    height: 20%;
    display: flex;
    align-items: center;
    margin: auto;
}

</style>
