# [GitHub官方的OpenGraph服务为每个Issue都自动生成了OpenGraph图片](https://github.com/myogg/Gitblog/issues/172)

先用最简单的调试一下。

```

<head>
    <!-- ... 其他meta标签 ... -->
    
    <!-- 主方案：GitHub OpenGraph -->
    <meta property="og:image" content="https://opengraph.githubassets.com/myogg/Gitblog/issues/{{issue.number}}">
    
    <!-- 备用方案：如果GitHub图片加载失败，用这个 -->
    <meta property="og:image:alt" content="{{issue.title}} - 北方的博客">
    
    <!-- 第二备用：本地默认图片（需要你先准备一张） -->
    <!--
    <meta property="og:image" 
          content="https://opengraph.githubassets.com/myogg/Gitblog/issues/{{issue.number}}"
          onerror="this.onerror=null; this.src='/static/default-og.png';">
    -->
</head>

```




