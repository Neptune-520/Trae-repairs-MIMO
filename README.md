# Trae-repairs-MIMO
临时修复trae使用mimo模型时无法问第二个问题，报错的问题

#### 要在powershell中运行！！！

### token-plan使用（api Key以tp开头）

1.下载proxy.py

2.安装依赖
```
pip install fastapi uvicorn httpx
```

3.运行
```
$env:UPSTREAM_API_KEY="你的api Key"
uvicorn proxy:app --host 127.0.0.1 --port 8000
```
4.在trae软件中添加模型里，自定义请求地址改为：```http://127.0.0.1:8000/v1```

### 其他计划（api Key以sk开头）

运行方式与token-plan一样，修改文件第十行内容：
```
UPSTREAM_BASE_URL = os.getenv("UPSTREAM_BASE_URL", "https://token-plan-cn.xiaomimimo.com")
```

```https://token-plan-cn.xiaomimimo.com```修改为```https://api.xiaomimimo.com```

不要带v1


