<template>
  <div class="bg">
    <el-container>
      <!--  顶栏    -->
      <el-header height="140px">
        <topbar></topbar>
      </el-header>

      <!--  底部容器   -->
      <el-container>
        <!--   侧边栏     -->
        <el-aside width="150px">
            <el-menu
              :default-active="page"
              class="el-menu-vertical-demo"
              @select="(index, indexPath)=>handleSelect(index, indexPath)"
              background-color="#2a4286"
              text-color="#fff"
              active-text-color="#ffd04b">

              <el-menu-item index="1" style="font-size: 18px; height: 56px; width: 150px; justify-content: center;align-content: space-around;">
                <i class="el-icon-menu"></i>
                <span slot="title">首页</span>
              </el-menu-item>

              <el-submenu index="2" style="font-size: 18px; width: 150px;">
                <template slot="title" style="font-size: 18px; width: 150px;line-height: 45px;">
                  <i class="el-icon-video-play" style="font-size: 18px;"></i>
                  <span style="font-size: 18px;">视频检测</span>
                </template>
                <el-menu-item-group style="width: 150px">
                  <template slot="title" style="display: none;"></template>
                  <el-menu-item index="2-1" style="font-size: 14px; width: 150px; height: 45px; ">空调漏氟检测</el-menu-item>
                  <el-menu-item index="2-2" style="font-size: 14px; width: 150px; height: 45px; ">电视机质量检测</el-menu-item>
                </el-menu-item-group>
              </el-submenu>

              <el-menu-item index="3" style="font-size: 18px; height: 56px; width: 150px;">
                <i class="el-icon-document"></i>
                <span slot="title">结果统计</span>
              </el-menu-item>
            </el-menu>

        </el-aside>

        <!--    主体内容    -->
        <el-main>
          <home v-if="page== '1'"></home>
          <result v-else-if="page=='3'"></result>
          <fog v-else-if="page=='2-1'"></fog>
          <tv v-else></tv>
        </el-main>
      </el-container>

    </el-container>
  </div>
</template>

<script>
import topbar from "@/components/topbar";
import home from "@/components/home";
import fog from "@/components/fog";
import result from "@/components/result";
import tv from "@/components/tv";

export default {
  name: "homepage",
  data(){
    return{
    }
  },
  components:{
    topbar, home, fog, result, tv
  },
  methods: {
      handleSelect(index, indexPath){
        // console.log('index:', index);
        // console.log('indexPath:', indexPath);
        this.$store.commit('pageChange', index)
      }
  },
  mounted() {
    // this.handleSelect(1, ['1']);
  },
  computed:{
    page: {
      get(){
        return String(this.$store.state.pageIndex);
      },
      set(value){
        this.handleSelect(value, [String(value)]);
      }
    }
  },
  watch:{
    page(oldVal, newVal){
      // console.log('page被修改了',newVal,oldVal,this)
    }
  }
}
</script>


<style scoped>
.bg{
  /*background-color: rgb(30, 30, 30);*/
  /*width: 1440px;*/
  /*height: 860px;*/
  width: 1080px;
  height: 645px;
}

/*  el-container布局 */
.el-header{
  background-color: #B3C0D1;
  color: #333;
  text-align: center;
  /*line-height: 140px;*/
  line-height: 105px;
  /*height: 140px;*/
  height: 105px;
  padding: 0;
  margin: 0;
}

.el-aside {
  background-color: #2a4286;
  color: #333;
  /*line-height: 720px;*/
  line-height: 540px;
}

.el-main {
  background-color: #E9EEF3;
  color: #333;
  line-height: 540px;
  /*width: 1240px;*/
  width: 930px;
  /*height: 720px;*/
  height: 540px;
  overflow: unset;
  margin: auto;
  padding: 10px;
}

::v-deep .el-submenu .el-menu-item-group__title {
    display: none;
}

::v-deep .el-submenu .el-menu-item {
    min-width: 150px ;
}

::v-deep .el-submenu .el-submenu__title .el-icon-arrow-down{
    font-size: 15px;
    position: static;
    margin: auto;
    padding-left: 6px;
}
</style>
