<template>
  <div id="app">
    <keep-alive>
      <router-view></router-view>
    </keep-alive>
  </div>
</template>

<script>
export default {
  name: 'app',
  created () {
      // 在页面加载时读取sessionStorage
      if (sessionStorage.getItem('store')) {
        this.$store.replaceState(Object.assign({}, this.$store.state, JSON.parse(sessionStorage.getItem('store'))))
      }
      // 在页面刷新时将store保存到sessionStorage里
      window.addEventListener('beforeunload', () => {
        sessionStorage.setItem('store', JSON.stringify(this.$store.state))
        // this.$store.commit('clearVideoList')
      })
  }
}
</script>

<style>
  html, body, #app{
    margin: 0;
    padding: 0;
    width: 100%;
    height: 100%;
  }

</style>
