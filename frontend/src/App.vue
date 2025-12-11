<template>
  <div id="app">
    <router-view />
  </div>
</template>

<script>
export default {
  name: 'App'
}
</script>

<style>
@font-face {
  font-family: 'Cubic_11';
  src: url('./assets/Cubic_11.woff2') format('woff2');
  font-weight: normal;
  font-style: normal;
  font-display: swap;
}

:root {
  --px-border-radius: 15px;
  --px-border: 3px;
}

#app {
  font-family: 'Cubic_11', Avenir, Helvetica, Arial, sans-serif;
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
  color: #2c3e50;
  margin: 0;
  padding: 0;
}

body {
  margin: 0;
  padding: 0;
  font-family: 'Cubic_11', Avenir, Helvetica, Arial, sans-serif;
  /* 全局禁止文字选择 */
  user-select: none;
  -webkit-user-select: none;
  -moz-user-select: none;
  -ms-user-select: none;
}

* {
  font-family: 'Cubic_11', Avenir, Helvetica, Arial, sans-serif;
}
</style>
