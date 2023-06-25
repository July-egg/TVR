<template>
  <div class="border">
    <div class="left">
      <h1>
        <img src="../assets/image/logo.png">
        <span style="padding-left: 20px">废旧电器回收智能管理平台</span>
      </h1>
    </div>

    <div class="right">
      <button @click="logout">
        退 出
        <br/>
        登 录
      </button>
    </div>
  </div>
</template>

<script>
export default {
  name: "topbar",
  methods:{
    logout(){
      console.log('退出登录')
      this.$router.push('/login')
    }
  }
}
</script>

<style scoped>
.border{
  width: 100%;
  height: 100%;
  background-color: #243a77;
  display: flex;
  align-items: center;
  justify-content: space-between;
  color: #ffffff;
  height: 140px;
}

h1{
  display: flex;
  align-items: center;
  font: normal 48px Cookie, Noto Sans, Helvetica, sans-serif;
  font-family: "PingFang SC";
  margin: 0;
  margin-left: 20px;
}

img{
  height:130px;
  padding-left: 10px;
  padding-right: 10px;
}

.right{
  margin-right: 40px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.right button{
  font-size: 20px;
  color: #ffffff;
  border: none;
  background: none;
  margin: auto;
  padding: 0;
  align-items: center;
  justify-content: center;
}

.right button:hover,
.right button:focus {
  color: white;
  border: 1px;
  border-color: #2a4286;
  outline: #ffffff;
}

</style>