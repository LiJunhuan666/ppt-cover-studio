# PPT Cover Studio · 高级中文PPT封面技能

从真实PPT与参考样式出发，制作中文艺术字、分层主视觉与精细封面。包含模板学习、内容保真、API配置、失败处理和413减负经验。适用于支持 `SKILL.md` 的AI编程助手；它是技能包，不是独立PPT桌面软件。

## 安装与使用

下载Release中的ZIP，解压后将 `ppt-cover-studio` 文件夹放入所用助手的技能目录。Codex通常使用 `$CODEX_HOME/skills`。需要D盘安装的用户可放在 `D:/CodexSkills/ppt-cover-studio`，然后在聊天中明确提供该目录的 `SKILL.md` 路径；是否自动发现取决于宿主，不保证自定义目录自动生效。

向助手提供自己的PPT、参考图或模板，并说：

> 使用 $ppt-cover-studio 制作这份PPT的中文封面，先确认完整标题和模板布局。生图服务、模型由我填写，输出PNG和可编辑PPTX；先给我一个封面初稿。

首次使用会询问网站、API基础地址、模型与输出要求。**不要把真实密钥发到聊天中。** 使用以下脚本在本机隐藏输入；本包不含任何作者密钥、不预设付费服务商。

```powershell
python -m pip install -r requirements.txt
python scripts/image_api.py configure --config D:/ppt-work/image-config.json
python scripts/image_api.py generate --config D:/ppt-work/image-config.json --prompt-file D:/ppt-work/prompt.txt --output D:/ppt-work/visual.png --size 1536x1024
python scripts/preview.py D:/ppt-work/visual.png D:/ppt-work/visual-preview.jpg
```

需Python 3.10+。配置过程不调用API；生成会使用你的服务商配额。配置文件只存地址和模型，生成时读取 `PPT_IMAGE_API_KEY` 或隐藏输入。按文档填写基础地址，不填写dashboard网址。具体兼容范围见 [API说明](references/api-configuration.md)。

## 包含内容

- `SKILL.md`：封面制作流程和约束。
- `references/`：源对话经验索引、201个脱敏记忆片段、提示词配方、API说明、验收清单。
- `scripts/`：同步文生图客户端及本地小预览生成。
- `tests/`：模拟网络测试，不调用真实生图API、不产生费用。

本包将指定长对话的可迁移经验按主题归档，不公开原始聊天、内部推理、密钥、个人附件和工具日志。历史中已经被否定的方案只作为失败经验。原对话覆盖多种任务，非封面任务不会自动激活对应媒体或聊天修复操作。

## 兼容与验证边界

生图脚本支持同步OpenAI兼容 `/images/generations` 的 `b64_json` / HTTPS URL响应；异步和图生图需单独适配。PPTX组装与渲染由宿主助手使用其可用工具完成，本包不自带PowerPoint、WPS、字体或商业模板。正文优先可编辑，API艺术字通常为位图。1536×1024是3:2；16:9封面应裁切重构或请求真正的16:9尺寸。

高质量需要检查准确的最终渲染与文字；小预览只能降低消息体积，不能保证永不413。本次发布只做本地模拟验证，未使用真实付费API检验任何服务商的当前可用性。

运行验证：`python -m unittest discover -s tests -v`。
