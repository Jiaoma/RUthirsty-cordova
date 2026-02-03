# 团队矛盾冲突模拟器

一个基于LLM的交互式游戏，通过角色扮演帮助团队成员理解跨团队协作中的沟通问题。

## 功能特点

- 🎮 交互式对话游戏体验
- 🤖 基于AI的动态对话生成
- 👥 多角色模拟真实团队场景
- 📊 可配置的游戏轮数和案例
- 🌐 Web界面，易于使用

## 技术栈

- **后端**: Python + Flask
- **前端**: HTML + CSS + JavaScript
- **AI**: OpenAI API (支持自定义API地址)

## 快速开始

### 1. 配置

编辑 `config.json` 文件，设置你的API信息：

```json
{
  "max_rounds": 10,
  "openai_api_base": "https://api.openai.com/v1",
  "openai_api_key": "your-api-key-here",
  "model": "gpt-4",
  "temperature": 0.8,
  "case_file": "cases/example_case.json"
}
```

### 2. 启动游戏

```bash
./start_game.sh
```

### 3. 访问游戏

在浏览器中打开: http://localhost:5000

## 目录结构

```
.
├── config.json              # 配置文件
├── start_game.sh           # 启动脚本
├── backend/
│   ├── app.py              # Flask后端服务
│   └── requirements.txt    # Python依赖
├── frontend/
│   └── index.html          # Web前端界面
└── cases/
    └── example_case.json   # 示例案例
```

## 自定义案例

你可以在 `cases/` 目录下创建新的案例文件。案例文件格式：

```json
{
  "title": "案例标题",
  "background": "案例背景描述",
  "characters": [
    {
      "name": "角色名",
      "role": "角色职位",
      "personality": "性格特点",
      "team": "所属团队"
    }
  ],
  "initial_dialogue": [
    {
      "speaker": "发言人",
      "content": "对话内容"
    }
  ],
  "player_role": "玩家扮演的角色名",
  "context": "当前情境描述"
}
```

## 游戏规则

1. 游戏分为多轮对话（可在config.json中配置最大轮数）
2. 每轮AI会提供4个对话选项（A、B、C、D）
3. 选项反映不同的沟通策略和情绪强度
4. AI会根据你的选择模拟其他角色的真实反应
5. 游戏结束时会提供总结和反思

## 依赖要求

- Python 3.7+
- pip
- 现代浏览器（Chrome、Firefox、Safari等）

## 故障排除

### 端口被占用

如果5000端口被占用，脚本会自动尝试关闭占用进程。如果仍有问题，可以手动修改 `backend/app.py` 中的端口号。

### API连接失败

请检查：
1. `config.json` 中的API地址和密钥是否正确
2. 网络连接是否正常
3. API服务是否可用

### 虚拟环境问题

如果遇到虚拟环境问题，可以删除 `venv` 目录后重新运行启动脚本。

## 许可证

MIT License