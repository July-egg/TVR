<template>
    <div class="login">
      <h1>
        <img src="../assets/image/logo_cut.png">
        <span style="padding-left: 20px"><b>废旧电器回收智能管理平台</b></span>
      </h1>

      <div class="warp">
          <div class="info">
              <div><h2>用 户 登 录</h2></div>

              <div class="user" style="display: flex; height: 70px; width: 370px; margin: auto; padding-top: 15px;">
                  <i class="el-icon-user" style="font-size: 40px; margin-right: 25px;"></i>
                  <el-autocomplete v-model="user" placeholder="请输入用户名" @change="userCg" style="width: 300px; height: 42px;"
                            :fetch-suggestions="queryUsr" @select="handleSelectUsr"></el-autocomplete>
              </div>
              <div class="user" style="display: flex; height: 70px; width: 370px; margin: auto; padding-top: 5px;">
                  <i class="el-icon-lock" style="font-size: 40px; margin-right: 25px;"></i>
                  <el-autocomplete v-model="pwd" placeholder="请输入密码" @change="pwdCg" style="width: 300px; height: 42px;"
                            :fetch-suggestions="queryPwd" @select="handleSelectPwd" type="password"></el-autocomplete>
              </div>

              <div class="log" style="margin: auto; display: flex; justify-content: center;">
                  <button style="color: #ffffff; background-color: #4095E5; font-size: 20px; margin-top: 30px;
                                    width: 125px; border-radius: 10px; padding: 5px; border: none;"
                          @click="login">
                      登 录
                  </button>
              </div>
          </div>

      </div>

      <h3>
        <span style="color: #ffffff; display: flex; justify-content: center; font-size: 15px;margin: auto;">
            <b>—————————•&nbsp;&nbsp;&nbsp;</b>深 圳 爱 析 科 技 有 限 责 任 公 司<b>&nbsp;&nbsp;&nbsp;•—————————</b>
        </span>
      </h3>
    </div>
</template>

<script>
export default {
    name: "login",
    data(){
        return{
            user:'',
            pwd:''
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
        }
    },

}
</script>

<style scoped>
.login{
    /*width: 1440px;*/
    /*height: 860px;*/
    width: 1080px;
    height: 645px;
    background-image: url("../assets/image/login.jpg");
    background-size:cover;
    align-items: center;
    justify-content: center;

    /*display: table-cell;*/
    vertical-align: middle;
    text-align: center;
    display: flex;
    flex-direction: column;
}

.warp{
    width: 800px;
    height: 300px;
    margin: 20px 140px;
    align-items: center;
    justify-content: center;
}

h1{
  display: flex;
  align-items: center;
  justify-content: center;
  padding-top: 40px;
  font: normal 48px Cookie, Noto Sans, Helvetica, sans-serif;
  font-family: sans-serif;;
  color: #ffffff;
  margin: auto;
}

img{
  height:80px;
}

.info{
    /*width: 550px;*/
    width: 413px;
    /*height: 330px;*/
    height: 225px;
    background-color: rgba(177, 203, 238, .6);
    align-items: center;
    justify-items: center;
    border-radius: 35px;
    margin: auto;
}

h3{
    display: flex;
    align-items: center;
    margin: auto;
    bottom: 40px;
}

h2{
    display: flex;
    justify-content: center;
    padding-top: 30px;
    font-size: 25px;
    color: #ffffff;
    margin: auto;
}
</style>
