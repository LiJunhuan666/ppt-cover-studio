# API配置与边界

首次询问：

- 服务商网站和文档网址，以及API基础地址（例如 `https://api.example.com/v1`，不是dashboard）。
- 准确模型名、所需尺寸、是否需要参考图编辑、允许生成的数量。
- 输出目录、封面内容、模板与交付格式。

不要把用户密钥贴入聊天。先在本机运行隐藏输入脚本：

```powershell
python scripts/image_api.py configure --config D:/ppt-work/image-config.json
python scripts/image_api.py generate --config D:/ppt-work/image-config.json --prompt-file D:/ppt-work/prompt.txt --output D:/ppt-work/cover.png --size 1536x1024
```

`configure`只保存基础地址和模型。`generate`从 `PPT_IMAGE_API_KEY` 读取密钥，缺失时隐藏输入；密钥仅用于本次请求。自动化可设置该环境变量，但不能在代码或终端历史中写真实密钥。首次生成将产生服务商费用；配置过程不调用API、不产生生图费用。

附带脚本支持：HTTPS基础地址、Bearer鉴权、JSON `POST <base>/images/generations`、`data[0].b64_json` 或公开HTTPS `data[0].url`。请求只发送model/prompt/n/size，不强制供应商可选字段。它验证实际图片，原子保存，并输出简短文件信息。

不支持：异步任务轮询、图生图multipart、带认证的下载链接、SDK专有格式。不要猜测替代接口；按文档新增经过验证的适配器。服务商报错不打印响应正文，以免服务端回显密钥；不自动重试、不自动切换模型，避免重复计费。

如需自定义尺寸、透明背景或编辑参考图，先核实文档与模型权限。用最少的已授权请求验证，不因一个模型报错而轮流测试大量模型。下载文件的URL必须是可公开访问的HTTPS地址；不要把Bearer密钥转发给图片下载域名。

历史中曾使用过CCTQ与HZAPI及不同模型。这些是过去的案例，不是本包推荐、担保或默认供应商。用户自己的配置优先。
